# SPDX-FileCopyrightText: Copyright (c) 2024-2026, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""Download local speech models into the persistent Docker model cache."""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import onnxruntime as ort
import requests
from faster_whisper import WhisperModel
from huggingface_hub import snapshot_download
from loguru import logger
from pipecat.services.kokoro.tts import KOKORO_CACHE_DIR, KOKORO_MODEL_URL, KOKORO_VOICES_URL

DEFAULT_WHISPER_MODEL = "deepdml/faster-whisper-large-v3-turbo-ct2"
MIN_KOKORO_MODEL_BYTES = 300_000_000
MIN_KOKORO_VOICES_BYTES = 20_000_000


def main() -> None:
    """Prefetch Faster Whisper and Kokoro artifacts before the voice server starts."""
    whisper_model = os.getenv("FASTER_WHISPER_MODEL", DEFAULT_WHISPER_MODEL).strip() or DEFAULT_WHISPER_MODEL
    token = os.getenv("HF_TOKEN", "").strip() or None
    max_workers = _positive_int(os.getenv("HF_DOWNLOAD_WORKERS"), default=1)

    logger.info(f"Prefetching Faster Whisper model {whisper_model!r}")
    whisper_path = snapshot_download(
        repo_id=whisper_model,
        token=token,
        max_workers=max_workers,
    )
    _verify_whisper_snapshot(Path(whisper_path))
    _verify_whisper_runtime(whisper_path)
    logger.info(f"Faster Whisper model ready at {whisper_path}")

    model_path = KOKORO_CACHE_DIR / "kokoro-v1.0.onnx"
    voices_path = KOKORO_CACHE_DIR / "voices-v1.0.bin"
    logger.info("Prefetching Kokoro model and voices")
    _download_if_missing_or_partial(KOKORO_MODEL_URL, model_path, MIN_KOKORO_MODEL_BYTES)
    _download_if_missing_or_partial(KOKORO_VOICES_URL, voices_path, MIN_KOKORO_VOICES_BYTES)
    _verify_kokoro_artifacts(model_path, voices_path)
    logger.info(f"Kokoro model ready at {KOKORO_CACHE_DIR}")


def _verify_whisper_snapshot(path: Path) -> None:
    """Fail startup when a partial Whisper snapshot lacks required files."""
    for filename in ("config.json", "model.bin", "tokenizer.json"):
        _verify_nonempty(path / filename)


def _verify_whisper_runtime(model_path: str) -> None:
    """Load Faster Whisper with the configured device to verify GPU startup."""
    device = os.getenv("FASTER_WHISPER_DEVICE", "cuda").strip() or "cuda"
    compute_type = os.getenv("FASTER_WHISPER_COMPUTE_TYPE", "float16").strip() or "float16"
    logger.info(f"Validating Faster Whisper with device={device}, compute_type={compute_type}")
    model = WhisperModel(model_path, device=device, compute_type=compute_type)
    del model


def _verify_nonempty(path: Path) -> None:
    """Require a downloaded artifact to exist and contain data."""
    if not path.is_file() or path.stat().st_size <= 0:
        raise RuntimeError(f"Required model artifact is missing or empty: {path}")


def _download_if_missing_or_partial(url: str, path: Path, minimum_bytes: int) -> None:
    """Atomically download an artifact when the cached copy is incomplete."""
    if path.is_file() and path.stat().st_size >= minimum_bytes:
        return
    if path.exists():
        logger.warning(f"Removing partial model artifact {path} ({path.stat().st_size} bytes)")
        path.unlink()

    path.parent.mkdir(parents=True, exist_ok=True)
    partial_path = path.with_name(f"{path.name}.part")
    partial_path.unlink(missing_ok=True)
    logger.info(f"Downloading {url} to {path}")
    try:
        with requests.get(url, stream=True, timeout=300) as response:
            response.raise_for_status()
            expected_bytes = int(response.headers.get("Content-Length") or 0)
            written = 0
            with partial_path.open("wb") as output:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        output.write(chunk)
                        written += len(chunk)
        if expected_bytes and written != expected_bytes:
            raise RuntimeError(f"Incomplete download for {path}: expected {expected_bytes} bytes, received {written}")
        if written < minimum_bytes:
            raise RuntimeError(f"Downloaded artifact is unexpectedly small: {path} ({written} bytes)")
        partial_path.replace(path)
    except Exception:
        partial_path.unlink(missing_ok=True)
        raise


def _verify_kokoro_artifacts(model_path: Path, voices_path: Path) -> None:
    """Parse both Kokoro artifacts with the configured runtime provider."""
    provider = os.getenv("ONNX_PROVIDER", "CUDAExecutionProvider").strip() or "CUDAExecutionProvider"
    available_providers = ort.get_available_providers()
    if provider not in available_providers:
        raise RuntimeError(f"Kokoro provider {provider!r} is unavailable; available: {available_providers}")
    try:
        session = ort.InferenceSession(str(model_path), providers=[provider])
        if provider not in session.get_providers():
            raise RuntimeError(f"Kokoro validation did not activate {provider!r}: {session.get_providers()}")
        np.load(voices_path, allow_pickle=False)
    except Exception:
        model_path.unlink(missing_ok=True)
        voices_path.unlink(missing_ok=True)
        raise


def _positive_int(raw: str | None, *, default: int) -> int:
    """Parse a positive integer with a safe default."""
    try:
        value = int(raw or "")
    except ValueError:
        return default
    return value if value > 0 else default


if __name__ == "__main__":
    main()
