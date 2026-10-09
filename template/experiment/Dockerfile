# Example run environment (machine-learning starter). The boundary it meets: the run
# installs exactly the frozen manifest committed in the source commit, with hashes
# verified, and runs code from the source commit only. Any image that meets the boundary
# is fine; edit freely.
#
# Build context: the experiment directory as of the source commit, for example extracted
# with `git archive <source-commit>:experiments/<id>` into a directory under .local/runs/.
# Build: docker build --build-arg RUN_ID=R001 -t <image> <context>

FROM python:3.12-slim

# uv, pinned to a release (or a digest, for stricter reproducibility).
COPY --from=ghcr.io/astral-sh/uv:0.12.23 /uv /uvx /bin/

ARG RUN_ID
WORKDIR /app

# Dependencies first, so the layer is reused across builds of the same manifest.
# --require-hashes rejects any line without a hash; --no-deps installs the manifest as is.
COPY runs/${RUN_ID}.requirements.txt /tmp/requirements.txt
RUN uv pip install --system --require-hashes --no-deps -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

# Shared libraries built as wheels (uv build --package <lib>) are installed here, for example:
# COPY wheels/ /tmp/wheels/
# RUN uv pip install --system --no-deps /tmp/wheels/*.whl

# The source archive: the experiment directory at the source commit.
COPY . /app/

# The launch command is the agent's choice and is recorded in the run record (`command`).
