# SPDX-FileCopyrightText: Copyright (c) 2024-2026, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""Session-local client for the Pi chief-of-staff agent service."""

from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import Awaitable, Callable
from contextlib import suppress
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from examples.frontend_backend_agent.src.protocol import ThinkerLifecycleEvent, response_hint


class PiAgentBackend:
    """Adapt one remote Pi AgentSession to the existing Talker tool boundary."""

    def __init__(self, base_url: str, *, timeout_seconds: float = 300.0) -> None:
        """Create an isolated Pi session client for one voice connection."""
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._session_id = uuid.uuid4().hex
        self._active_task: asyncio.Task[dict[str, Any]] | None = None

    async def call(
        self,
        query: str,
        slots: dict[str, Any] | None = None,
        *,
        on_started: Callable[[ThinkerLifecycleEvent], Awaitable[None]] | None = None,
    ) -> dict[str, Any]:
        """Send a user request to the session's Pi chief-of-staff instance."""
        del slots
        clean_query = query.strip()
        call_id = uuid.uuid4().hex[:12]
        event = ThinkerLifecycleEvent(marker="ThinkerStarted", call_id=call_id, query=clean_query)
        if on_started:
            await on_started(event)

        task = asyncio.create_task(
            asyncio.to_thread(
                self._request,
                "POST",
                f"/sessions/{self._session_id}/messages",
                {"message": clean_query},
            )
        )
        self._active_task = task
        try:
            result = await task
        except asyncio.CancelledError:
            await self._abort_remote()
            raise
        finally:
            if self._active_task is task:
                self._active_task = None

        response_text = str(result.get("response") or "").strip()
        if not response_text:
            return response_hint(
                reason="empty_agent_response",
                action="retry",
                response_text="I completed the request but did not receive a response. Please try again.",
                context="chief_of_staff",
            )
        return response_hint(
            reason="agent_completed",
            action="answer_directly",
            response_text=response_text,
            context="chief_of_staff",
        )

    def cancel_active(self, reason: str = "new_user_query") -> bool:
        """Cancel the local wait; ``call`` propagates cancellation to Pi."""
        del reason
        task = self._active_task
        if task is None or task.done():
            return False
        task.cancel()
        return True

    def cancel_pending_booking(self) -> bool:
        """Satisfy the shared backend protocol; Pi has no pending booking draft."""
        return False

    async def _abort_remote(self) -> None:
        # Cancellation must not be replaced by an abort transport failure.
        with suppress(Exception):
            await asyncio.shield(
                asyncio.to_thread(
                    self._request,
                    "POST",
                    f"/sessions/{self._session_id}/abort",
                    {},
                )
            )

    def _request(self, method: str, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        request = Request(
            f"{self._base_url}{path}",
            data=body,
            headers={"Content-Type": "application/json"},
            method=method,
        )
        try:
            with urlopen(request, timeout=self._timeout_seconds) as response:  # noqa: S310 - configured service URL
                decoded = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Pi agent service returned HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise RuntimeError(f"Pi agent service is unavailable at {self._base_url}: {exc.reason}") from exc
        except json.JSONDecodeError as exc:
            raise RuntimeError("Pi agent service returned invalid JSON") from exc
        if not isinstance(decoded, dict):
            raise RuntimeError("Pi agent service returned an invalid response object")
        return decoded
