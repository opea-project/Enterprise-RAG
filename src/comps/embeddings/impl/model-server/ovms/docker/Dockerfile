# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
FROM openvino/model_server:2024.4
USER root

# Install Python and other dependencies (git) to be able to install 
RUN apt-get update && \
    apt-get install -y python3 python3-pip python-is-python3 git

RUN python -m pip install openvino_tokenizers==2024.4.0
RUN python -m pip install "optimum-intel @ git+https://github.com/huggingface/optimum-intel.git@7a224c2419240d5fb58f2f75c2e29f179ed6da28"

RUN cp -r /usr/local/lib/python3.10/dist-packages/openvino_tokenizers /ovms/lib/python/openvino_tokenizers
RUN cp -r /usr/local/lib/python3.10/dist-packages/openvino_tokenizers-2024.4.0.0.dist-info  /ovms/lib/python/openvino_tokenizers-2024.4.0.0.dist-info 

# Replace libopenvino_tokenizers.so with the one distributed with the image
RUN cp /ovms/lib/libopenvino_tokenizers.so /ovms/lib/python/openvino_tokenizers/lib/libopenvino_tokenizers.so

WORKDIR /home/ovms
COPY docker/entrypoint.sh /home/ovms/entrypoint.sh
COPY ./combine_models.py /home/ovms/combine_models.py
RUN chmod +x /home/ovms/entrypoint.sh

# Cleanup
RUN pip cache purge && rm -rf /tmp/tmp* /var/lib/apt/lists/*

ENTRYPOINT ["./entrypoint.sh"]

