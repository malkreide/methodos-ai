"""The one place a ChromaDB client is constructed.

`chromadb.PersistentClient` is not safe to construct concurrently in one
process. Chroma keeps one shared "system" per path and starts it on first
use; two threads that both arrive first both start it, and one of them gets
a half-initialised system. That surfaced as `/health` answering 500
(`'RustBindingsAPI' object has no attribute 'bindings'`, or "Could not
connect to tenant default_tenant") when the Docker health check and a
first browser request hit a freshly started server at the same moment.

Construction is serialised here; everything after it is left to Chroma.
Once the shared system exists, a further `PersistentClient(path)` reuses it
and returns in about a millisecond, so the lock costs nothing in steady state.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

_construct_lock = threading.Lock()


def persistent_client(path: Path) -> Any:
    """A PersistentClient for `path`, safe to call from any number of threads."""
    import chromadb

    with _construct_lock:
        return chromadb.PersistentClient(path=str(path))
