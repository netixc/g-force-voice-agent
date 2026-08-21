# SPDX-FileCopyrightText: Copyright (c) 2024-2026, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""Ava cascaded pipeline: STT -> Chief-of-Staff Talker -> Pi agent -> TTS."""

from __future__ import annotations

import asyncio
import os

from dotenv import load_dotenv
from loguru import logger
from pipecat.frames.frames import LLMRunFrame, TTSUpdateSettingsFrame
from pipecat.observers.user_bot_latency_observer import UserBotLatencyObserver
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.worker import PipelineParams, PipelineWorker
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import (
    LLMContextAggregatorPair,
)
from pipecat.processors.frameworks.rtvi.frames import RTVIServerMessageFrame
from pipecat.runner.types import RunnerArguments
from pipecat.services.nvidia.llm import NvidiaLLMService, NvidiaLLMSettings
from pipecat.services.nvidia.stt import NvidiaSTTService, NvidiaSTTSettings
from pipecat.services.nvidia.tts import NvidiaTTSService, NvidiaTTSSettings
from pipecat.transcriptions.language import Language
from pipecat.transports.base_transport import TransportParams
from pipecat.workers.runner import WorkerRunner

import examples_registry
from examples.frontend_backend_agent.src.ava_tools import TOOLS_SCHEMA as AVA_TOOLS_SCHEMA
from examples.frontend_backend_agent.src.pi_backend import PiAgentBackend
from examples.frontend_backend_agent.src.tool_handlers import build_handlers
from examples.shared.audio_recorder import create_audio_recorder
from examples.shared.nemotron_speech_text_filter import NemotronSpeechTextFilter
from examples.shared.pipeline_utils import build_user_aggregator_params
from tracing import IS_TRACING_ENABLED
from utils import (
    is_nvcf,
    load_ipa_dictionary,
    load_service_entry,
    normalize_lang_code,
    parse_env_float,
    parse_env_int,
    parse_json_dict,
    resolve_prompt,
)

load_dotenv(override=True)

CHAT_HISTORY_RECENT_TURNS = parse_env_int("CHAT_HISTORY_RECENT_TURNS", 20)
AGENT_FILLER_THRESHOLD_SECONDS = parse_env_float("AGENT_FILLER_THRESHOLD_SECONDS", 0.3, min_value=0.0)
IN_PROCESS_SERVICE_SERVER = "in-process"
OPENROUTER_BASE_HOST = "openrouter.ai"


def _is_in_process_service(server: str) -> bool:
    """Return whether a catalog service runs inside the pipeline process."""
    return server.strip().lower() == IN_PROCESS_SERVICE_SERVER


def _is_openrouter_endpoint(base_url: str) -> bool:
    """Return whether an LLM base URL targets OpenRouter."""
    return OPENROUTER_BASE_HOST in base_url.lower()


def _llm_connection_kwargs(base_url: str) -> dict:
    """Build provider-aware authentication and optional request headers."""
    if not _is_openrouter_endpoint(base_url):
        return {"api_key": os.getenv("NVIDIA_API_KEY"), "base_url": base_url}

    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is required for the selected OpenRouter LLM")

    headers: dict[str, str] = {}
    http_referer = os.getenv("OPENROUTER_HTTP_REFERER", "").strip()
    app_name = os.getenv("OPENROUTER_APP_NAME", "Chief OS").strip()
    if http_referer:
        headers["HTTP-Referer"] = http_referer
    if app_name:
        headers["X-OpenRouter-Title"] = app_name

    kwargs: dict = {"api_key": api_key, "base_url": base_url}
    if headers:
        kwargs["default_headers"] = headers
    return kwargs


def _resolve_onnx_provider(available_providers: list[str]) -> str:
    """Resolve and validate the Kokoro ONNX execution provider."""
    provider = os.getenv("ONNX_PROVIDER", "CPUExecutionProvider").strip() or "CPUExecutionProvider"
    if provider not in available_providers:
        raise RuntimeError(
            f"Kokoro ONNX provider {provider!r} is unavailable; available providers: {available_providers}"
        )
    return provider


def _language(code: str, default: Language = Language.EN_US) -> Language:
    """Resolve a catalog language code to a Pipecat language enum."""
    normalized = normalize_lang_code(code.strip()) if code else default.value
    try:
        return Language(normalized)
    except ValueError:
        base = normalized.split("-", 1)[0]
        try:
            return Language(base)
        except ValueError:
            logger.warning(f"Unsupported local speech language {code!r}; using {default.value}")
            return default


def _build_context_messages(base_prompt: str, system_prompt: str = "") -> list[dict]:
    """Build initial Talker context messages."""
    if system_prompt:
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": base_prompt},
        ]
    return [{"role": "system", "content": base_prompt}]


def _apply_chat_history_sliding_window(
    context: LLMContext,
    preserve_prompt_messages: int,
    chat_history_limit: int,
) -> None:
    """Keep the prompt messages and latest conversation turns."""
    if chat_history_limit < 1:
        return
    messages = context.get_messages()
    preserve = max(0, preserve_prompt_messages)
    if len(messages) <= preserve + chat_history_limit:
        return
    context.set_messages(messages[:preserve] + messages[preserve:][-chat_history_limit:])


async def bot(runner_args: RunnerArguments) -> None:
    """Build and run the Frontend/Backend Agent cascaded pipeline for one session."""
    logger.info("Starting Frontend/Backend Agent cascaded pipeline")
    transport = _create_transport(runner_args)
    body = runner_args.body if isinstance(runner_args.body, dict) else {}
    welcome_enabled = examples_registry.welcome_message_enabled(body.get("pipeline_mode", ""))

    prompt_key, talker_prompt = resolve_prompt(
        __file__,
        body.get("prompt_content", ""),
        body.get("prompt_key", ""),
    )
    default_llm = load_service_entry("llm", "")
    default_tts = load_service_entry("tts", "")
    default_asr = load_service_entry("asr", "")

    # --- ASR ---
    asr_server = body.get("asr_server", "") or default_asr.get("server", "grpc.nvcf.nvidia.com:443")
    asr_function_id = body.get("asr_function_id", "") or default_asr.get("function_id", "")
    asr_model = body.get("asr_model", "") or default_asr.get("model", "")
    asr_language_code = body.get("asr_language_code", "") or default_asr.get("language_code", "")
    if _is_in_process_service(asr_server):
        from pipecat.services.whisper.stt import Model as WhisperModel
        from pipecat.services.whisper.stt import WhisperSTTService

        asr_model = asr_model or WhisperModel.LARGE_V3_TURBO.value
        stt = WhisperSTTService(
            device=os.getenv("FASTER_WHISPER_DEVICE", "cuda"),
            compute_type=os.getenv("FASTER_WHISPER_COMPUTE_TYPE", "float16"),
            settings=WhisperSTTService.Settings(
                model=asr_model,
                language=_language(asr_language_code),
                no_speech_prob=parse_env_float("FASTER_WHISPER_NO_SPEECH_PROB", 0.4, min_value=0.0),
            ),
        )
        logger.info(
            f"ASR: provider=faster-whisper, model={asr_model}, "
            f"device={os.getenv('FASTER_WHISPER_DEVICE', 'cuda')}, "
            f"compute_type={os.getenv('FASTER_WHISPER_COMPUTE_TYPE', 'float16')}, "
            f"language={asr_language_code or 'en-US'}"
        )
    else:
        asr_ssl = is_nvcf(asr_server)
        asr_kwargs: dict = {
            "api_key": os.getenv("NVIDIA_API_KEY"),
            "server": asr_server,
            "use_ssl": asr_ssl,
        }
        if asr_function_id or asr_model:
            asr_kwargs["model_function_map"] = {
                "function_id": asr_function_id,
                "model_name": asr_model or "custom-asr",
            }
        if asr_language_code:
            asr_kwargs["settings"] = NvidiaSTTSettings(language=asr_language_code)
        stt = NvidiaSTTService(**asr_kwargs, stop_history=400)
        logger.info(
            f"ASR: provider=nvidia, server={asr_server}, ssl={asr_ssl}, "
            f"function_id={asr_function_id or '(default)'}, language={asr_language_code or '(default)'}"
        )

    # --- Talker LLM ---
    model_id = body.get("model_id", "") or default_llm.get("model_id", "nvidia/nemotron-3-nano-30b-a3b")
    base_url = body.get("base_url", "") or default_llm.get("base_url", "https://integrate.api.nvidia.com/v1")
    system_prompt = body.get("system_prompt", "") or default_llm.get("system_prompt", "")
    talker_max_tokens = _parse_optional_int(body.get("max_tokens", "") or default_llm.get("max_tokens"), 2048)
    extra_params = parse_json_dict(
        body.get("extra_params", "") or default_llm.get("extra_params", ""),
        label="extra_params",
    )
    llm_settings = NvidiaLLMSettings(model=model_id, max_tokens=talker_max_tokens)
    if extra_params:
        llm_settings.extra = extra_params
    talker_llm = NvidiaLLMService(
        **_llm_connection_kwargs(base_url),
        settings=llm_settings,
    )
    logger.info(
        f"Talker LLM: model={model_id}, base_url={base_url}, prompt={prompt_key}, "
        f"system_prompt={'<' + system_prompt + '>' if system_prompt else '(none)'}, "
        f"max_tokens={talker_max_tokens}, "
        f"extra_params={extra_params or '(none)'}"
    )

    default_agent_server = load_service_entry("agent-server", "")
    agent_server_url = os.getenv("PI_AGENT_URL", "").strip() or str(
        default_agent_server.get("server") or "http://localhost:8787"
    )
    backend_timeout = parse_env_float("PI_AGENT_TIMEOUT_SECONDS", 300.0, min_value=1.0)
    backend = PiAgentBackend(agent_server_url, timeout_seconds=backend_timeout)
    logger.info(f"Agent backend: pi, server={agent_server_url}, timeout={backend_timeout:.1f}s")

    logger.info(f"Agent filler threshold: {AGENT_FILLER_THRESHOLD_SECONDS:.3f}s")
    for name, handler in build_handlers(
        backend,
        filler_threshold_seconds=AGENT_FILLER_THRESHOLD_SECONDS,
    ).items():
        cancel_on_interruption = name != "call_backend"
        talker_llm.register_function(
            name,
            handler,
            cancel_on_interruption=cancel_on_interruption,
            timeout_secs=backend_timeout,
        )
        logger.info(f"Registered Talker tool: {name}, cancel_on_interruption={cancel_on_interruption}")

    # --- TTS ---
    tts_server = body.get("tts_server", "") or default_tts.get("server", "grpc.nvcf.nvidia.com:443")
    tts_ssl = is_nvcf(tts_server)
    tts_voice = body.get("tts_voice_id", "") or default_tts.get("voice_id", "")
    tts_synthesis_mode = body.get("tts_synthesis_mode", "")
    raw_tts_function_id = body.get("tts_function_id")
    tts_function_id = (
        str(raw_tts_function_id) if raw_tts_function_id is not None else default_tts.get("function_id", "")
    )
    tts_model = body.get("tts_model", "") or default_tts.get("model", "")
    tts_zero_shot_audio_prompt_file = body.get("tts_zero_shot_audio_prompt_file", "") or default_tts.get(
        "zero_shot_audio_prompt_file", ""
    )
    tts_language_code = body.get("tts_language_code", "") or default_tts.get("language_code", "")
    tts_is_in_process = _is_in_process_service(tts_server)
    if tts_is_in_process:
        import onnxruntime as ort
        from pipecat.services.kokoro.tts import KokoroTTSService

        onnx_provider = _resolve_onnx_provider(ort.get_available_providers())
        tts_voice = tts_voice or "af_heart"
        tts = KokoroTTSService(
            settings=KokoroTTSService.Settings(
                voice=tts_voice,
                language=_language(tts_language_code),
            ),
            text_filters=[NemotronSpeechTextFilter()],
        )
        _resolve_onnx_provider(tts._kokoro.sess.get_providers())
        logger.info(
            f"TTS: provider=kokoro, execution_provider={onnx_provider}, voice={tts_voice}, "
            f"model={tts_model or 'kokoro-v1.0'}, language={tts_language_code or 'en-US'}"
        )
    else:
        custom_dictionary = load_ipa_dictionary()
        tts_settings_kwargs: dict = {"voice": tts_voice}
        if tts_synthesis_mode:
            tts_settings_kwargs["synthesis_mode"] = tts_synthesis_mode
        tts_kwargs: dict = {
            "api_key": os.getenv("NVIDIA_API_KEY"),
            "server": tts_server,
            "settings": NvidiaTTSSettings(**tts_settings_kwargs),
            "use_ssl": tts_ssl,
            "text_filters": [NemotronSpeechTextFilter()],
            "custom_dictionary": custom_dictionary,
        }
        if tts_function_id or tts_model:
            tts_kwargs["model_function_map"] = {
                "function_id": tts_function_id,
                "model_name": tts_model,
            }
        if tts_zero_shot_audio_prompt_file:
            tts_kwargs["zero_shot_audio_prompt_file"] = tts_zero_shot_audio_prompt_file
        tts = NvidiaTTSService(**tts_kwargs)
        logger.info(
            f"TTS: provider=nvidia, server={tts_server}, ssl={tts_ssl}, voice={tts_voice}, "
            f"model={tts_model or '(pipecat default)'}, function_id={tts_function_id or '(pipecat default)'}, "
            f"synthesis_mode={tts_synthesis_mode or '(pipecat default)'}, "
            f"zero_shot_audio_prompt_file={tts_zero_shot_audio_prompt_file or '(none)'}"
        )

    # --- Context + aggregators ---
    messages = _build_context_messages(talker_prompt, system_prompt)
    context = LLMContext(messages, tools=AVA_TOOLS_SCHEMA, tool_choice="auto")
    preserve_prompt_messages = len(messages)
    user_aggregator, assistant_aggregator = LLMContextAggregatorPair(
        context,
        user_params=build_user_aggregator_params(welcome_enabled),
    )
    audio_recorder = create_audio_recorder()

    pipeline = Pipeline(
        [
            transport.input(),
            stt,
            user_aggregator,
            talker_llm,
            tts,
            transport.output(),
            *([audio_recorder] if audio_recorder else []),
            assistant_aggregator,
        ]
    )

    latency_observer = UserBotLatencyObserver()
    summary_lock = asyncio.Lock()

    @assistant_aggregator.event_handler("on_assistant_turn_stopped")
    async def on_assistant_turn_stopped(aggregator, message):
        async with summary_lock:
            _apply_chat_history_sliding_window(context, preserve_prompt_messages, CHAT_HISTORY_RECENT_TURNS)

    @latency_observer.event_handler("on_first_bot_speech_latency")
    async def on_first_bot_speech(observer, latency):
        logger.info(f"First bot speech latency: {latency:.3f}s")
        await task.queue_frame(
            RTVIServerMessageFrame(data={"type": "user-bot-latency", "latency": round(latency, 3), "first": True})
        )

    @latency_observer.event_handler("on_latency_measured")
    async def on_latency(observer, latency):
        logger.info(f"User-to-bot latency: {latency:.3f}s")
        await task.queue_frame(
            RTVIServerMessageFrame(data={"type": "user-bot-latency", "latency": round(latency, 3), "first": False})
        )

    task = PipelineWorker(
        pipeline,
        params=PipelineParams(enable_metrics=True, enable_usage_metrics=True),
        idle_timeout_secs=runner_args.pipeline_idle_timeout_secs,
        observers=[latency_observer],
        enable_tracing=IS_TRACING_ENABLED,
    )

    @user_aggregator.event_handler("on_user_turn_stopped")
    async def on_user_turn_stopped(aggregator, strategy, message):
        await task.queue_frame(
            RTVIServerMessageFrame(
                data={
                    "type": "user-turn-finalized",
                    "timestamp": getattr(message, "timestamp", None),
                    "transcript": getattr(message, "content", None),
                    "user_id": getattr(message, "user_id", None),
                }
            )
        )

    @task.rtvi.event_handler("on_client_ready")
    async def on_client_connected(rtvi):
        logger.info("Client connected")
        if audio_recorder:
            await audio_recorder.start_recording()
        if not welcome_enabled:
            logger.info("Welcome message disabled; waiting for the user to speak first")
            return
        context.add_message({"role": "user", "content": "Please greet the user briefly."})
        await task.queue_frames([LLMRunFrame()])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info("Client disconnected")
        await task.cancel()

    async def _apply_set_voice(payload: dict) -> None:
        voice_id = payload.get("voice_id", "")
        language = payload.get("language", "")
        if not voice_id:
            return
        settings_kwargs: dict = {"voice": voice_id}
        if tts_is_in_process:
            from pipecat.services.kokoro.tts import KokoroTTSService

            if language:
                settings_kwargs["language"] = _language(language)
            settings_delta = KokoroTTSService.Settings(**settings_kwargs)
        else:
            if language:
                settings_kwargs["language"] = normalize_lang_code(language)
            settings_delta = NvidiaTTSSettings(**settings_kwargs)
        await task.queue_frame(TTSUpdateSettingsFrame(delta=settings_delta, service=tts))
        logger.info(f"Voice switched to {voice_id}, language={settings_kwargs.get('language', '(unchanged)')}")

    @task.rtvi.event_handler("on_client_message")
    async def on_client_message(rtvi, message):
        payload = message.data if isinstance(message.data, dict) else {}
        if message.type == "set-voice":
            await _apply_set_voice(payload)

    runner = WorkerRunner(handle_sigint=runner_args.handle_sigint)
    await runner.add_workers(task)
    await runner.run()


def _create_transport(runner_args: RunnerArguments):
    """Create a transport from runner arguments."""
    from pipecat.runner.types import EvalRunnerArguments, SmallWebRTCRunnerArguments

    if isinstance(runner_args, SmallWebRTCRunnerArguments):
        from pipecat.transports.smallwebrtc.transport import SmallWebRTCTransport

        return SmallWebRTCTransport(
            params=TransportParams(
                audio_in_enabled=True,
                audio_out_enabled=True,
                audio_out_10ms_chunks=parse_env_int("AUDIO_OUT_10MS_CHUNKS", 5),
            ),
            webrtc_connection=runner_args.webrtc_connection,
        )

    if isinstance(runner_args, EvalRunnerArguments):
        from pipecat.evals.serializer import RTVIEvalSerializer
        from pipecat.evals.transport import EvalTransport, EvalTransportParams

        return EvalTransport(
            params=EvalTransportParams(
                audio_in_enabled=True,
                audio_in_sample_rate=16000,
                audio_out_enabled=True,
                audio_out_sample_rate=16000,
                audio_out_10ms_chunks=parse_env_int("AUDIO_OUT_10MS_CHUNKS", 10),
                add_wav_header=False,
                serializer=RTVIEvalSerializer(),
            ),
            host=runner_args.host,
            port=runner_args.port,
        )

    from pipecat.serializers.base_serializer import FrameSerializer
    from pipecat.serializers.protobuf import ProtobufFrameSerializer
    from pipecat.transports.websocket.fastapi import (
        FastAPIWebsocketParams,
        FastAPIWebsocketTransport,
    )

    websocket = getattr(runner_args, "websocket", None)
    if websocket is None:
        raise TypeError(f"Unsupported runner args type: {type(runner_args)}")

    return FastAPIWebsocketTransport(
        websocket=websocket,
        params=FastAPIWebsocketParams(
            audio_in_enabled=True,
            audio_in_sample_rate=16000,
            audio_out_enabled=True,
            audio_out_sample_rate=16000,
            audio_out_10ms_chunks=parse_env_int("AUDIO_OUT_10MS_CHUNKS", 10),
            add_wav_header=False,
            serializer=ProtobufFrameSerializer(params=FrameSerializer.InputParams(ignore_rtvi_messages=False)),
        ),
    )


def _parse_optional_int(raw: object, default: int) -> int:
    """Parse optional integer config values."""
    if raw in (None, ""):
        return default
    try:
        return int(raw)
    except (TypeError, ValueError):
        logger.warning(f"Invalid integer config value {raw!r}; using {default}")
        return default
