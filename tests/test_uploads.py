import io
import zipfile

import pytest

from methodos.uploads import (
    MAX_DOCX_XML_BYTES,
    NoTextError,
    UnsupportedFileError,
    UploadError,
    detect_kind,
    extract_document_text,
    normalise,
)
from tests.conftest import make_docx, make_pdf


@pytest.mark.parametrize(
    ("name", "head", "kind"),
    [
        ("Handout.PDF", b"%PDF-1.7", "pdf"),
        ("notes.docx", b"PK\x03\x04", "docx"),
        ("notes.md", b"# Lean", "text"),
        ("talk.m4a", b"\x00\x00\x00 ftyp", "audio"),
        ("workshop.mp4", b"\x00\x00\x00 ftyp", "video"),
    ],
)
def test_detect_kind_by_extension(name, head, kind):
    assert detect_kind(name, head) == kind


def test_detect_kind_catches_a_renamed_file():
    with pytest.raises(UnsupportedFileError, match="not a PDF"):
        detect_kind("fake.pdf", b"PK\x03\x04")


def test_detect_kind_explains_legacy_word_files():
    with pytest.raises(UnsupportedFileError, match=r"\.docx"):
        detect_kind("old.doc", b"\xd0\xcf\x11\xe0")


def test_detect_kind_lists_what_is_accepted():
    with pytest.raises(UnsupportedFileError, match=r"\.pdf"):
        detect_kind("photo.jpg", b"\xff\xd8")


def test_pdf_text_is_extracted(tmp_path):
    pytest.importorskip("pypdf", reason="needs the `api` extra")
    path = tmp_path / "a.pdf"
    path.write_bytes(make_pdf(["Lean Coffee", "Topics are voted on, then timeboxed."]))
    text = extract_document_text(path, "pdf")
    assert "Lean Coffee" in text
    assert "timeboxed" in text


def test_a_pdf_without_text_is_called_a_scan(tmp_path):
    pytest.importorskip("pypdf", reason="needs the `api` extra")
    path = tmp_path / "scan.pdf"
    path.write_bytes(make_pdf([]))
    with pytest.raises(NoTextError, match="scan"):
        extract_document_text(path, "pdf")


def test_a_broken_pdf_is_an_upload_error_not_a_crash(tmp_path):
    pytest.importorskip("pypdf", reason="needs the `api` extra")
    path = tmp_path / "broken.pdf"
    path.write_bytes(b"%PDF-1.4\nthis is not a pdf body")
    with pytest.raises(UploadError):
        extract_document_text(path, "pdf")


def test_docx_paragraphs_are_extracted(tmp_path):
    path = tmp_path / "a.docx"
    path.write_bytes(make_docx(["Lean Coffee", "Alle schreiben Themen auf & stimmen ab."]))
    assert extract_document_text(path, "docx") == (
        "Lean Coffee\nAlle schreiben Themen auf & stimmen ab."
    )


def test_a_zip_that_is_not_word_is_refused(tmp_path):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("hello.txt", "hi")
    path = tmp_path / "a.docx"
    path.write_bytes(buf.getvalue())
    with pytest.raises(UploadError, match=r"document\.xml"):
        extract_document_text(path, "docx")


def test_a_docx_that_inflates_too_far_is_refused(tmp_path):
    """The upload limit says nothing about what a zip unpacks to."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("word/document.xml", "<a>" + " " * (MAX_DOCX_XML_BYTES + 1) + "</a>")
    path = tmp_path / "bomb.docx"
    path.write_bytes(buf.getvalue())
    assert path.stat().st_size < 1024 * 1024
    with pytest.raises(UploadError, match="too large"):
        extract_document_text(path, "docx")


def test_text_files_in_utf8_and_windows_encoding(tmp_path):
    utf8 = tmp_path / "a.txt"
    utf8.write_bytes("﻿Grösse und Mass".encode())
    legacy = tmp_path / "b.txt"
    legacy.write_bytes("Grösse und Mass".encode("cp1252"))
    assert extract_document_text(utf8, "text") == "Grösse und Mass"
    assert extract_document_text(legacy, "text") == "Grösse und Mass"


def test_an_empty_text_file_has_no_text(tmp_path):
    path = tmp_path / "empty.md"
    path.write_text("  \n\n ", encoding="utf-8")
    with pytest.raises(NoTextError):
        extract_document_text(path, "text")


def test_normalise_keeps_paragraphs_and_drops_the_rest():
    assert normalise("a\u00a0 b\r\n\r\n\r\n\r\n  c \t d ") == "a b\n\nc d"
