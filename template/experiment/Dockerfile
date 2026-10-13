# syntax=docker/dockerfile:1
# Example run environment (machine-learning starter). The boundaries it meets: the run
# installs exactly the frozen manifest committed in the source commit, with hashes
# verified, and runs code from the source commit only; dependencies and source sit in
# separate layers, and the dependency layer is keyed by the manifest's content alone.
# Any image that meets the boundaries is fine; edit freely.
#
# Build context: for a Formal Run, the experiment directory as of the source commit
# (`just run <R###> ...` in this directory extracts it with git archive and builds); for
# informal runs, the working tree (`just build`).

# Keep the base image and the uv release as the starter has them unless the plan says why:
# every layer below is shared between Experiments only while these lines are the same.
FROM python:3.12-slim

# uv, pinned to a release (or a digest, for stricter reproducibility).
COPY --from=ghcr.io/astral-sh/uv:0.12.23 /uv /uvx /bin/

# Step 1: dependencies. Only requirements.txt is visible here (mounted, not copied), so
# this layer is reused by every round and every Experiment whose manifest has the same
# content; the cache mount keeps downloaded wheels when the manifest does change.
# --require-hashes rejects any line without a hash; --no-deps installs the manifest as is.
#
# With PyTorch, name the accelerator backend exactly, the same one the manifest was frozen
# with (`just freeze <exp-id> cuXXX`): add --torch-backend=cuXXX matching the driver of the
# machine that runs, or --torch-backend=cpu. Never auto: it is decided by the machine that
# builds.
ENV UV_LINK_MODE=copy UV_CACHE_DIR=/var/cache/uv
RUN --mount=type=bind,source=requirements.txt,target=/tmp/requirements.txt \
    --mount=type=cache,target=/var/cache/uv \
    uv pip install --system --require-hashes --no-deps -r /tmp/requirements.txt

# Shared libraries built as wheels (uv build --package <lib>) are installed here, for example:
# COPY wheels/ /tmp/wheels/
# RUN uv pip install --system --no-deps /tmp/wheels/*.whl

# Step 2: source, the experiment directory at the source commit. From one round to the
# next this is the only step whose input changes, so a rebuild starts here.
WORKDIR /app
COPY . /app/

# The launch command is the agent's choice and is recorded in the run record (`command`).
