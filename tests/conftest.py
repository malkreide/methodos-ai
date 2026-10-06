"""Shared test fixtures: deterministic provider fakes and tmp Chroma."""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from pathlib import Path

import pytest


class FakeLLM:
    """Deterministic LLM fake. Records calls for assertions."""

    name = "fake-llm"

    def __init__(self, response: str = "stub explanation") -> None:
        self.response = response
        self.calls: list[tuple[str, str]] = []

    def complete(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> str:
        self.calls.append((system, user))
        return self.response


class FakeEmbedding:
    """Deterministic embedding fake.

    Vector = first `dimensions` bytes of sha256(text), normalized to [0, 1].
    Same text → same vector → same Chroma ranking.
    """

    def __init__(self, dimensions: int = 4) -> None:
        self.name = f"fake-embedding-{dimensions}d"
        self.dimensions = dimensions

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        out: list[list[float]] = []
        for t in texts:
            h = hashlib.sha256(t.encode("utf-8")).digest()
            out.append([b / 255.0 for b in h[: self.dimensions]])
        return out


class FakeReranker:
    """Deterministic rerank fake: score = number of query terms in the document.

    Lexical overlap deliberately disagrees with FakeEmbedding's sha256 ordering,
    so a test can tell whether reranking actually reordered anything rather than
    happening to agree with retrieval.
    """

    name = "fake-reranker"

    def __init__(self) -> None:
        self.calls: list[tuple[str, list[str]]] = []

    def score(self, query: str, documents: Sequence[str]) -> list[float]:
        self.calls.append((query, list(documents)))
        terms = {t for t in query.lower().split() if t}
        return [float(sum(1 for t in terms if t in doc.lower())) for doc in documents]


@pytest.fixture
def fake_llm() -> FakeLLM:
    return FakeLLM()


@pytest.fixture
def fake_reranker() -> FakeReranker:
    return FakeReranker()


@pytest.fixture
def fake_embedding() -> FakeEmbedding:
    return FakeEmbedding(dimensions=8)


@pytest.fixture
def tmp_chroma_path(tmp_path: Path) -> Path:
    """A clean Chroma directory for each test."""
    p = tmp_path / "chroma"
    p.mkdir()
    return p


class FakeTranscriber:
    """Deterministic transcription fake: returns a fixed text, enforces the length limit."""

    name = "fake-transcriber"

    def __init__(self, text: str = "Alle schreiben Themen auf.", duration: float = 60.0) -> None:
        self.text = text
        self.duration = duration
        self.calls: list[Path] = []

    def transcribe(self, path: Path, *, max_seconds: float):  # type: ignore[no-untyped-def]
        from methodos.providers.base import MediaTooLongError, Transcript

        self.calls.append(path)
        assert path.exists(), "the file must still be on disk while it is transcribed"
        if self.duration > max_seconds:
            raise MediaTooLongError(f"{self.duration}s > {max_seconds}s")
        return Transcript(text=self.text, duration_seconds=self.duration, language="de")


def make_pdf(lines: Sequence[str]) -> bytes:
    """A minimal valid one-page PDF with the given lines as real text (Helvetica).

    Written by hand rather than with a library so the tests need nothing beyond
    the reader they exercise; offsets in the xref table are computed, not typed.
    """
    stream = (
        "BT /F1 12 Tf 72 720 Td 14 TL "
        + " ".join(
            "(" + ln.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)") + ") '"
            for ln in lines
        )
        + " ET"
    )
    objects = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        "/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        f"<< /Length {len(stream.encode('latin-1'))} >>\nstream\n{stream}\nendstream",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
    ]
    out = b"%PDF-1.4\n"
    offsets = []
    for i, body in enumerate(objects, 1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n{body}\nendobj\n".encode("latin-1")
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    out += b"".join(f"{o:010d} 00000 n \n".encode() for o in offsets)
    out += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    )
    return out


def make_docx(paragraphs: Sequence[str]) -> bytes:
    """A minimal .docx: just enough of the OOXML package for word/document.xml to be read."""
    import io
    import zipfile
    from xml.sax.saxutils import escape

    body = "".join(f"<w:p><w:r><w:t>{escape(p)}</w:t></w:r></w:p>" for p in paragraphs)
    doc = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{body}</w:body></w:document>"
    )
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("[Content_Types].xml", "<Types/>")
        z.writestr("word/document.xml", doc)
    return buf.getvalue()
