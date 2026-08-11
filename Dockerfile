# Methodos AI as a self-contained HTTP service.
#
# Two things are baked in at build time, both so that a started container needs
# no egress except to the LLM provider:
#
#   * the sentence-transformers weights (~160MB across the embedding model and
#     the cross-encoder), which otherwise download from HuggingFace on the
#     first query and would make a cold start look like a hang;
#   * CPU-only torch, because the GPU wheels are several gigabytes and nothing
#     here would use them.
#
# The Chroma index is deliberately *not* baked in. It is a derived artifact
# (architectural principle 3) and the entrypoint rebuilds it on every start, so
# a mounted `methods/` directory is always what the container is actually
# serving — an image whose index silently predates its catalog is the one
# failure mode that would be invisible from the outside.

FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/opt/hf

WORKDIR /build
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy only what the build backend needs before the source, so a change to a
# method JSON does not invalidate the dependency layer.
COPY pyproject.toml constraints.txt README.md ./
COPY src ./src

# The CPU index is an *extra* index, not a replacement: everything except torch
# still resolves from PyPI.
RUN pip install --extra-index-url https://download.pytorch.org/whl/cpu \
        ".[api,local]" -c constraints.txt

# Warm the model cache. Names must match the defaults in config.py; overriding
# METHODOS_EMBEDDING_MODEL or METHODOS_RERANK_MODEL at run time is supported but
# then costs a download on first use.
RUN python -c "\
from sentence_transformers import CrossEncoder, SentenceTransformer; \
SentenceTransformer('all-MiniLM-L6-v2'); \
CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')"


FROM python:3.12-slim

ENV PATH="/opt/venv/bin:$PATH" \
    HF_HOME=/opt/hf \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    METHODOS_METHODS_DIR=/app/methods \
    METHODOS_CHROMA_PATH=/data/chroma \
    METHODOS_FEEDBACK_PATH=/data/feedback.jsonl

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /opt/hf /opt/hf

WORKDIR /app
COPY methods ./methods
# verify_explain.py answers a question only a live deployment can be asked:
# whether the model actually honours the reranked order. See the README.
COPY scripts ./scripts
COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh

# /data holds the two things that must survive a rebuild in opposite ways: the
# index (rewritten every start) and the feedback log (append-only, the whole
# point of running this long enough to improve it).
RUN chmod +x /usr/local/bin/entrypoint.sh \
    && useradd --create-home --uid 10001 methodos \
    && mkdir -p /data \
    && chown -R methodos:methodos /data /app
USER methodos

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request,sys; \
sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4).status == 200 else 1)"

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["uvicorn", "methodos.api:app", "--host", "0.0.0.0", "--port", "8000"]
