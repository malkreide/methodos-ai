"""Read the text out of an uploaded file, so a proposal can start from it.

What comes in is whatever someone had at hand: a PDF handout, a Word
document, notes in a text file, a recording of a workshop. What goes out is
plain text for a person to read and an LLM to draft from — never the file.
The caller holds the file in a temporary directory and deletes it the moment
this module is done with it; nothing here writes anywhere.

Documents are read in-process. Audio and video go through a
TranscriptionProvider, which by contract runs locally (see
`providers/base.py`): recordings from schools and offices carry the voices of
people who never agreed to send them to a cloud service.

Not supported, on purpose: legacy `.doc`, scanned PDFs (no OCR) and images.
Each is refused with a message saying what to do instead, rather than
returning an empty draft that looks like the method had nothing to say.
"""

from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import Literal
from xml.etree import ElementTree

Kind = Literal["pdf", "docx", "text", "audio", "video"]

DOCUMENT_SUFFIXES: dict[str, Kind] = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".txt": "text",
    ".md": "text",
}
AUDIO_SUFFIXES = frozenset({".mp3", ".m4a", ".wav", ".ogg", ".oga", ".opus", ".flac", ".aac"})
VIDEO_SUFFIXES = frozenset({".mp4", ".m4v", ".mov", ".webm", ".mkv", ".avi"})

ACCEPTED_SUFFIXES = tuple(sorted({*DOCUMENT_SUFFIXES, *AUDIO_SUFFIXES, *VIDEO_SUFFIXES}))

MAX_PDF_PAGES = 200
MAX_DOCX_XML_BYTES = 20 * 1024 * 1024
"""Uncompressed size of word/document.xml. A zip is easy to inflate into
gigabytes; the upload limit alone says nothing about what it unpacks to."""

_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


class UploadError(ValueError):
    """The file cannot be turned into text. The message is shown to the person."""


class UnsupportedFileError(UploadError):
    pass


class NoTextError(UploadError):
    pass


def detect_kind(filename: str, head: bytes) -> Kind:
    """The kind of file, by extension, cross-checked against its first bytes.

    The extension decides because browsers send unreliable content types; the
    magic bytes catch a renamed file before a parser chokes on it with a less
    helpful error.
    """
    suffix = Path(filename).suffix.lower()
    if suffix in DOCUMENT_SUFFIXES:
        kind = DOCUMENT_SUFFIXES[suffix]
        if kind == "pdf" and not head.startswith(b"%PDF"):
            raise UnsupportedFileError("the file is named .pdf but is not a PDF")
        if kind == "docx" and not head.startswith(b"PK"):
            raise UnsupportedFileError("the file is named .docx but is not a Word document")
        return kind
    if suffix in AUDIO_SUFFIXES:
        return "audio"
    if suffix in VIDEO_SUFFIXES:
        return "video"
    if suffix == ".doc":
        raise UnsupportedFileError(
            "old Word files (.doc) are not supported — save it as .docx or PDF first"
        )
    raise UnsupportedFileError(
        f"unsupported file type {suffix or '(none)'!r}. Accepted: {', '.join(ACCEPTED_SUFFIXES)}"
    )


def extract_document_text(path: Path, kind: Kind) -> str:
    """Plain text of a PDF, Word or text file. Raises UploadError with a readable reason."""
    if kind == "pdf":
        text = _pdf_text(path)
    elif kind == "docx":
        text = _docx_text(path)
    elif kind == "text":
        text = _plain_text(path)
    else:
        raise ValueError(f"{kind} is not a document; transcribe it instead")
    text = normalise(text)
    if not text:
        if kind == "pdf":
            raise NoTextError(
                "the PDF contains no text — probably a scan. Upload the original "
                "document or describe the method in the form instead."
            )
        raise NoTextError("the file contains no text")
    return text


def normalise(text: str) -> str:
    """Collapse the whitespace extraction leaves behind, keep paragraph breaks."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub("[ \t\u00a0]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _pdf_text(path: Path) -> str:
    from pypdf import PdfReader
    from pypdf.errors import PdfReadError

    try:
        reader = PdfReader(str(path))
        if reader.is_encrypted and not reader.decrypt(""):
            raise UploadError("the PDF is password-protected")
        pages = reader.pages[:MAX_PDF_PAGES]
        return "\n\n".join(page.extract_text() or "" for page in pages)
    except UploadError:
        raise
    except (PdfReadError, ValueError, KeyError, OSError) as e:
        raise UploadError(f"the PDF could not be read: {e}") from e


def _docx_text(path: Path) -> str:
    try:
        with zipfile.ZipFile(path) as z:
            try:
                info = z.getinfo("word/document.xml")
            except KeyError:
                raise UploadError("not a Word document (word/document.xml is missing)") from None
            if info.file_size > MAX_DOCX_XML_BYTES:
                raise UploadError("the Word document is too large to read")
            root = ElementTree.fromstring(z.read(info))
    except UploadError:
        raise
    except (zipfile.BadZipFile, ElementTree.ParseError, OSError) as e:
        raise UploadError(f"the Word document could not be read: {e}") from e

    paragraphs: list[str] = []
    for p in root.iter(f"{_W}p"):
        parts: list[str] = []
        for el in p.iter():
            if el.tag == f"{_W}t" and el.text:
                parts.append(el.text)
            elif el.tag == f"{_W}tab":
                parts.append("\t")
            elif el.tag in (f"{_W}br", f"{_W}cr"):
                parts.append("\n")
        paragraphs.append("".join(parts))
    return "\n".join(paragraphs)


def _plain_text(path: Path) -> str:
    raw = path.read_bytes()
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        # Windows-1252: what a text file saved on an office PC most likely is.
        return raw.decode("cp1252", errors="replace")
