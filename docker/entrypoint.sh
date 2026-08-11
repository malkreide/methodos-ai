#!/bin/sh
# Rebuild the index, then hand over to the container's command.
#
# Ingest runs on every start rather than at build time because Chroma is a
# derived artifact and `methods/` is a bind mount: the catalog the operator
# edited must be the catalog the server answers from, without a rebuild. It
# costs a few seconds for the shipped 23-method catalog, with the embedding
# model already resident in the image.
#
# METHODOS_SKIP_INGEST=1 opts out. That is for one-off `docker compose run`
# commands sharing the index volume with a running server: two processes
# writing the same Chroma directory is the one way to corrupt it.
set -eu

if [ "${METHODOS_SKIP_INGEST:-0}" = "1" ]; then
    echo "entrypoint: METHODOS_SKIP_INGEST=1 — using the existing index" >&2
else
    echo "entrypoint: rebuilding the index from ${METHODOS_METHODS_DIR:-methods}" >&2
    methodos ingest --methods-dir "${METHODOS_METHODS_DIR:-methods}"
fi

exec "$@"
