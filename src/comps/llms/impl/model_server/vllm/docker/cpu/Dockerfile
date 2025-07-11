# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM public.ecr.aws/q9t5s3a7/vllm-cpu-release-repo:v0.9.2 as dev
# Default value 1000 for Kubernetes user
# Overridable for local/testing builds to set same as host user
ARG USER_UID=1000

RUN useradd -u ${USER_UID} -m -s /bin/bash user        \
&& chown -R user /home/user /tmp

USER user
WORKDIR /home/user

COPY docker/assign_cores.sh .

ENTRYPOINT ["python3", "-m", "vllm.entrypoints.openai.api_server"]
