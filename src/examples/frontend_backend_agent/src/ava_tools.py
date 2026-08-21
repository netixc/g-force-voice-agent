# SPDX-FileCopyrightText: Copyright (c) 2024-2026, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""Tools available to Ava for delegating work to the Pi backend."""

from __future__ import annotations

from pipecat.adapters.schemas.tools_schema import AdapterType, ToolsSchema

CALL_BACKEND_TOOL: dict = {
    "type": "function",
    "function": {
        "name": "call_backend",
        "description": (
            "Delegate the user's complete request to their persistent primary Pi agent. "
            "Use this for questions, research, project work, and follow-up requests."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The user's request, preserving concrete names, paths, commands, and constraints.",
                },
                "filler_text": {
                    "type": "string",
                    "description": "A short neutral sentence to speak only when the agent takes longer than expected.",
                },
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
}

CANCEL_BACKEND_TOOL: dict = {
    "type": "function",
    "function": {
        "name": "cancel_backend",
        "description": "Stop the active delegated Pi request when the user asks to stop or cancel.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    },
}

TOOLS_SCHEMA = ToolsSchema(
    standard_tools=[], custom_tools={AdapterType.OPENAI: [CALL_BACKEND_TOOL, CANCEL_BACKEND_TOOL]}
)
