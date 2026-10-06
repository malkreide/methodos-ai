"""Speech to text with faster-whisper (CTranslate2, CPU, offline once the model is cached)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from methodos.providers.base import (
    MediaTooLongError,
    TranscriberUnavailableError,
    Transcript,
    TranscriptionError,
)

DEFAULT_MODEL = "small"


def _load_whisper(model_name: str) -> Any:
    """Indirection so tests can patch this single function."""
    from faster_whisper import WhisperModel

    # int8 on CPU: roughly half the memory of float32 for a quality loss that
    # does not matter for a draft somebody is going to read and edit anyway.
    return WhisperModel(model_name, device="cpu", compute_type="int8")


def _probe_duration(path: Path) -> float | None:
    """Seconds of audio, read from the container header without decoding it.

    PyAV comes with faster-whisper and ships its own FFmpeg, so video
    containers (mp4, mov, webm) open here as well — only their audio track is
    ever decoded.
    """
    import av

    try:
        with av.open(str(path)) as container:
            if not container.streams.audio:
                raise TranscriptionError("the file has no audio track")
            if container.duration is None:
                return None
            return float(container.duration / av.time_base)
    except TranscriptionError:
        raise
    except Exception as e:
        raise TranscriptionError(f"not a readable audio or video file: {e}") from e


class FasterWhisperTranscriber:
    """Lazy-loaded Whisper model. Nothing leaves the machine.

    The model downloads into Hugging Face's cache on first use (the Docker
    image bakes it in). Language is detected per file, so a German recording
    yields German text without configuration.
    """

    def __init__(self, model_name: str = DEFAULT_MODEL) -> None:
        self.name = f"faster-whisper:{model_name}"
        self._model_name = model_name
        self._model: Any = None

    def _ensure_loaded(self) -> None:
        if self._model is None:
            try:
                self._model = _load_whisper(self._model_name)
            except Exception as e:
                raise TranscriberUnavailableError(f"failed to load {self._model_name}: {e}") from e

    def transcribe(self, path: Path, *, max_seconds: float) -> Transcript:
        duration = _probe_duration(path)
        if duration is not None and duration > max_seconds:
            raise MediaTooLongError(
                f"the recording is {duration / 60:.0f} minutes long; "
                f"the limit is {max_seconds / 60:.0f}"
            )
        self._ensure_loaded()
        try:
            # beam_size=1 is about twice as fast as the default 5 on a CPU, and
            # the request is waiting. Not conditioning on the previous text
            # stops Whisper's known habit of looping on a phrase in long
            # silences; the VAD filter skips those silences in the first place.
            segments, info = self._model.transcribe(
                str(path),
                beam_size=1,
                vad_filter=True,
                condition_on_previous_text=False,
            )
            if duration is None and info.duration > max_seconds:
                raise MediaTooLongError(
                    f"the recording is {info.duration / 60:.0f} minutes long; "
                    f"the limit is {max_seconds / 60:.0f}"
                )
            # `segments` is lazy: the actual transcription happens here.
            text = " ".join(s.text.strip() for s in segments if s.text.strip())
        except TranscriptionError:
            raise
        except Exception as e:
            raise TranscriptionError(f"transcription failed: {e}") from e
        return Transcript(
            text=text,
            duration_seconds=float(info.duration),
            language=getattr(info, "language", None),
        )
