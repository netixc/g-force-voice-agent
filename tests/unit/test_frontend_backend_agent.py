# SPDX-FileCopyrightText: Copyright (c) 2024-2026, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: BSD-2-Clause

# ruff: noqa: D100, D101, D102

import unittest
from unittest.mock import patch

from pipecat.frames.frames import LLMFullResponseEndFrame, LLMFullResponseStartFrame, LLMTextFrame
from pipecat.services.llm_service import FunctionCallParams

from examples.frontend_backend_agent import pipeline
from examples.frontend_backend_agent.src.protocol import AgentLifecycleEvent, is_speakable_payload, response_hint
from examples.frontend_backend_agent.src.tool_handlers import _normalize_arguments, build_handlers


class _FrameCapturingLLM:
    def __init__(self) -> None:
        self.frames = []

    async def push_frame(self, frame) -> None:
        self.frames.append(frame)


class _Agent:
    def __init__(self, *, active: bool = False) -> None:
        self.active = active
        self.calls = []

    async def call(self, query, slots=None, *, on_started=None):
        self.calls.append((query, slots))
        if on_started:
            await on_started(AgentLifecycleEvent(marker="AgentStarted", call_id="test", query=query))
        return response_hint(
            reason="agent_completed",
            action="answer_directly",
            response_text="The Pi chief completed the task.",
            context="chief_of_staff",
        )

    def cancel_active(self, reason="new_user_query"):
        del reason
        was_active = self.active
        self.active = False
        return was_active


class PipelineConfigTests(unittest.TestCase):
    def test_service_detection(self):
        self.assertTrue(pipeline._is_in_process_service("in-process"))
        self.assertFalse(pipeline._is_in_process_service("localhost:50051"))

    def test_openrouter_detection(self):
        self.assertTrue(pipeline._is_openrouter_endpoint("https://openrouter.ai/api/v1"))
        self.assertFalse(pipeline._is_openrouter_endpoint("https://integrate.api.nvidia.com/v1"))

    def test_context_uses_single_system_message_without_override(self):
        self.assertEqual(
            pipeline._build_context_messages("You are Ava."), [{"role": "system", "content": "You are Ava."}]
        )

    def test_context_preserves_explicit_system_override(self):
        self.assertEqual(
            pipeline._build_context_messages("Prompt", "System"),
            [{"role": "system", "content": "System"}, {"role": "user", "content": "Prompt"}],
        )


class ProtocolTests(unittest.TestCase):
    def test_response_hint_is_speakable(self):
        payload = response_hint(reason="done", action="answer", response_text="Done.", context="chief_of_staff")
        self.assertTrue(is_speakable_payload(payload))

    def test_empty_response_is_not_speakable(self):
        payload = response_hint(reason="aborted", action="stop", response_text="", context="chief_of_staff")
        self.assertFalse(is_speakable_payload(payload))

    def test_wrapped_arguments_are_normalized(self):
        self.assertEqual(_normalize_arguments({"original_args": '{"query":"status"}'}), {"query": "status"})


class ToolHandlerTests(unittest.IsolatedAsyncioTestCase):
    async def test_call_backend_sends_request_to_agent(self):
        agent = _Agent()
        llm = _FrameCapturingLLM()
        results = []

        async def result_callback(result, *, properties=None):
            results.append((result, properties))

        params = FunctionCallParams(
            function_name="call_backend",
            tool_call_id="call-test",
            arguments={"query": "Review the workspace"},
            llm=llm,
            pipeline_worker=None,
            context=None,
            result_callback=result_callback,
        )
        with patch.dict("os.environ", {"FRONTEND_BACKEND_DIRECT_TOOL_RESPONSE": "true"}):
            await build_handlers(agent)["call_backend"](params)

        self.assertEqual(agent.calls, [("Review the workspace", {})])
        self.assertEqual(results[0][0]["context"], "chief_of_staff")
        self.assertIsInstance(llm.frames[0], LLMFullResponseStartFrame)
        self.assertIsInstance(llm.frames[1], LLMTextFrame)
        self.assertIsInstance(llm.frames[2], LLMFullResponseEndFrame)

    async def test_call_backend_requires_query(self):
        results = []

        async def result_callback(result, *, properties=None):
            results.append((result, properties))

        params = FunctionCallParams(
            function_name="call_backend",
            tool_call_id="call-test",
            arguments={},
            llm=_FrameCapturingLLM(),
            pipeline_worker=None,
            context=None,
            result_callback=result_callback,
        )
        await build_handlers(_Agent())["call_backend"](params)
        self.assertEqual(results[0][0]["reason"], "params_missing")

    async def test_cancel_backend_stops_active_agent(self):
        results = []

        async def result_callback(result, *, properties=None):
            results.append((result, properties))

        params = FunctionCallParams(
            function_name="cancel_backend",
            tool_call_id="cancel-test",
            arguments={},
            llm=_FrameCapturingLLM(),
            pipeline_worker=None,
            context=None,
            result_callback=result_callback,
        )
        await build_handlers(_Agent(active=True))["cancel_backend"](params)
        self.assertEqual(results[0][0]["reason"], "cancelled")


if __name__ == "__main__":
    unittest.main()
