# Base image intentionally uses "base" (not python) because the Python
# environment and dependencies are managed via pixi, not system Python.
FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04

# Use bash for RUN so pipefail is supported.
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ARG PIXI_VERSION=v0.84.1
ARG PIXI_SHA256_X86_64=c81a16595e9e925fac3b12fe50cedbf415619a421ad2b72c1bba2a6ba6c2454a
ARG PIXI_SHA256_AARCH64=0595613aedd95f84f90a55ba4b51fc1e4b86afb4eaa3e34ca3f3454d8f22c2e6

# curl, git, tar, and ca-certificates are provided by the devcontainers
# base image, so no apt install step is needed.

# Install pixi, verifying the download against the pinned SHA256 above.
RUN set -eu \
    && ARCH="$(uname -m)" \
    && case "${ARCH}" in \
        x86_64) PIXI_ARCH="x86_64"; PIXI_SHA256="${PIXI_SHA256_X86_64}" ;; \
        aarch64|arm64) PIXI_ARCH="aarch64"; PIXI_SHA256="${PIXI_SHA256_AARCH64}" ;; \
        *) echo "Unsupported architecture: ${ARCH}" >&2; exit 1 ;; \
       esac \
    && PIXI_ASSET="pixi-${PIXI_ARCH}-unknown-linux-musl.tar.gz" \
    && PIXI_BASE_URL="https://github.com/prefix-dev/pixi/releases/download/${PIXI_VERSION}" \
    && curl -fsSL --compressed -o /tmp/pixi.tar.gz "${PIXI_BASE_URL}/${PIXI_ASSET}" \
    && echo "${PIXI_SHA256}  /tmp/pixi.tar.gz" | sha256sum -c - \
    && tar -xzf /tmp/pixi.tar.gz -C /tmp pixi \
    && install -m 0755 /tmp/pixi /usr/local/bin/pixi \
    && rm -f /tmp/pixi /tmp/pixi.tar.gz

ENV SHELL=/bin/bash \
    PATH=/home/vscode/.local/bin:/home/vscode/.opencode/bin:${PATH}

USER vscode

RUN echo 'eval "$(pixi completion -s bash)"' >> /home/vscode/.bashrc

# Pre-install the coding agent CLIs (Claude Code, Codex, Copilot CLI, OpenCode)
# during the image build so the devcontainer is ready on attach.
COPY --chown=vscode:vscode install-agents.sh /tmp/install-agents.sh
RUN bash /tmp/install-agents.sh && rm -f /tmp/install-agents.sh
