# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Use the official Python image from the Docker Hub
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.5.26 /uv /uvx /bin/

# Add non-root user
RUN useradd -m -s /bin/bash user

USER user
ENV PATH="$PATH:/home/user/.local/bin"
ENV PYTHONPATH="/home/user"

# Copy the dependencies file into the container
WORKDIR /home/user
COPY ./edp/app/pyproject.toml pyproject.toml
COPY ./edp/app/uv.lock uv.lock

# --locked will fail when any changes in pyproject.toml were introduced
# Source: https://github.com/astral-sh/uv/blob/main/docs/concepts/projects/sync.md#checking-if-the-lockfile-is-up-to-date
RUN uv sync --locked --no-cache
ENV PATH="/home/user/.venv/bin:$PATH"

# Copy the rest of the application code into the container
COPY --chown=user:user ./edp/app ./app
COPY --chown=user:user ./comps/cores/mega/logger.py ./comps/cores/mega/logger.py

# Expose the port the app runs on
EXPOSE 5000

# Set workdir
WORKDIR /home/user/app
# Define the command to run the application
CMD ["bash"]
