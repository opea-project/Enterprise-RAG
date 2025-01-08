# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Use the official Python image from the Docker Hub
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Add non-root user
RUN useradd -m -s /bin/bash user

USER user
ENV PATH="$PATH:/home/user/.local/bin"
ENV PYTHONPATH="/home/user"

# Copy the requirements file into the container
COPY ./edp/app/requirements.txt /tmp/requirements.txt

# Install the dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# Copy the rest of the application code into the container
WORKDIR /home/user
COPY --chown=user:user ./edp/app ./app
COPY --chown=user:user ./comps/cores/mega/logger.py ./comps/cores/mega/logger.py

# Expose the port the app runs on
EXPOSE 5000

# Set workdir
WORKDIR /home/user/app
# Define the command to run the application
CMD ["bash"]
