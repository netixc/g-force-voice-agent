# SPDX-FileCopyrightText: Copyright (c) 2024-2026, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: BSD-2-Clause

# ruff: noqa: D100, D101, D102

import asyncio
import unittest
from unittest.mock import patch

from examples.frontend_backend_agent.src.pi_backend import PiAgentBackend


class PiAgentBackendTests(unittest.IsolatedAsyncioTestCase):
    async def test_call_returns_speakable_pi_response(self):
        backend = PiAgentBackend("http://pi-agent:8787")
        events = []

        async def on_started(event):
            events.append(event)

        with patch.object(backend, "_request", return_value={"response": "I reviewed your priorities."}) as request:
            payload = await backend.call("Review my priorities", on_started=on_started)

        self.assertEqual(payload["response_text"], "I reviewed your priorities.")
        self.assertEqual(payload["context"], "chief_of_staff")
        self.assertEqual(events[0].marker, "AgentStarted")
        self.assertIn("/sessions/", request.call_args.args[1])
        request_payload = request.call_args.args[2]
        self.assertEqual(request_payload["message"], "Review my priorities")
        self.assertEqual(request_payload["request_id"], events[0].call_id)

    async def test_empty_agent_response_has_retry_message(self):
        backend = PiAgentBackend("http://pi-agent:8787")
        with patch.object(backend, "_request", return_value={"response": ""}):
            payload = await backend.call("Hello")

        self.assertEqual(payload["reason"], "empty_agent_response")
        self.assertEqual(payload["action"], "retry")

    async def test_cancel_active_cancels_local_request_and_aborts_remote(self):
        backend = PiAgentBackend("http://pi-agent:8787")
        request_started = asyncio.Event()
        release_request = asyncio.Event()
        requests = []

        def blocking_request(method, path, payload):
            requests.append((method, path, payload))
            if path.endswith("/messages"):
                request_started_loop.call_soon_threadsafe(request_started.set)
                asyncio.run_coroutine_threadsafe(release_request.wait(), request_started_loop).result(timeout=2)
                return {"response": "late"}
            return {"aborted": True}

        request_started_loop = asyncio.get_running_loop()
        with patch.object(backend, "_request", side_effect=blocking_request):
            task = asyncio.create_task(backend.call("Long task"))
            await asyncio.wait_for(request_started.wait(), timeout=1)
            self.assertTrue(backend.cancel_active())
            with self.assertRaises(asyncio.CancelledError):
                await task
            release_request.set()
            await asyncio.sleep(0.05)

        message_request = next(item for item in requests if item[1].endswith("/messages"))
        abort_request = next(item for item in requests if item[1].endswith("/abort"))
        self.assertEqual(abort_request[2]["request_id"], message_request[2]["request_id"])


if __name__ == "__main__":
    unittest.main()
