# SPDX-FileCopyrightText: Copyright (c) 2024-2026, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: BSD-2-Clause

FROM node:22-bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    git \
    ripgrep \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pi-agent-service/package.json pi-agent-service/package-lock.json ./
RUN npm ci --omit=dev --ignore-scripts

COPY pi-agent-service/models.json ./models.json
COPY pi-agent-service/src/ ./src/

RUN mkdir -p /workspace /agent-data \
    && chown -R node:node /workspace /agent-data

USER node

EXPOSE 8787

CMD ["node", "src/server.mjs"]
