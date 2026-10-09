# Environment of this Experiment's runs. The build context is this directory as of the commit
# being run (for a Formal Run: the source commit, extracted with git archive).
FROM python@sha256:05cda9777409a9c3ffddd94a4c476b79f0769a0b4857f0c7ed9226b6800b0d6f
COPY --from=ghcr.io/astral-sh/uv:0.12.23 /uv /bin/uv
ARG RUN_ID
COPY runs/${RUN_ID}.requirements.txt /tmp/requirements.txt
RUN uv pip install --system --require-hashes --no-deps --no-cache -r /tmp/requirements.txt
WORKDIR /app
COPY train.py design.json /app/
ENV PYTHONUNBUFFERED=1 HOME=/tmp HF_HUB_OFFLINE=1 TRACKIO_STORAGE_MODE=sqlite
ENTRYPOINT ["python", "/app/train.py"]
