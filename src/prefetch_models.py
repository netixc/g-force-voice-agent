# SPDX-FileCopyrightText: Copyright (c) 2024-2026, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""Download local speech models into the persistent Docker model cache."""

from __future__ import annotations

import os
from pathlib import Path

from huggingface_hub import snapshot_download
from loguru import logger
from pipecat.services.kokoro.tts import KOKORO_CACHE_DIR, _ensure_model_files

DEFAULT_WHISPER_MODEL = "deepdml/faster-whisper-large-v3-turbo-ct2"


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
    logger.info(f"Faster Whisper model ready at {whisper_path}")

    model_path = KOKORO_CACHE_DIR / "kokoro-v1.0.onnx"
    voices_path = KOKORO_CACHE_DIR / "voices-v1.0.bin"
    logger.info("Prefetching Kokoro model and voices")
    _ensure_model_files(model_path, voices_path)
    _verify_nonempty(model_path)
    _verify_nonempty(voices_path)
    logger.info(f"Kokoro model ready at {KOKORO_CACHE_DIR}")


def _verify_whisper_snapshot(path: Path) -> None:
    """Fail startup when a partial Whisper snapshot lacks required files."""
    for filename in ("config.json", "model.bin", "tokenizer.json"):
        _verify_nonempty(path / filename)


def _verify_nonempty(path: Path) -> None:
    """Require a downloaded artifact to exist and contain data."""
    if not path.is_file() or path.stat().st_size <= 0:
        raise RuntimeError(f"Required model artifact is missing or empty: {path}")


def _positive_int(raw: str | None, *, default: int) -> int:
    """Parse a positive integer with a safe default."""
    try:
        value = int(raw or "")
    except ValueError:
        return default
    return value if value > 0 else default


if __name__ == "__main__":
    main()
