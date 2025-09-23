FROM openvino/model_server:2025.0
COPY --from=ghcr.io/astral-sh/uv:0.6.7 /uv /uvx /bin/

ENV LANG=C.UTF-8

# Ensure the existing user with UID 1000 has ownership of necessary directories
USER root
RUN mkdir -p /data /model /home/ovms && \
    chown -R 1000:1000 /data /model /home/ovms

RUN rm -rf /ovms/python_deps/

# Copy files and set permissions as root
COPY docker/entrypoint.sh /home/ovms/entrypoint.sh
COPY ./combine_models.py /home/ovms/combine_models.py
RUN chmod +x /home/ovms/entrypoint.sh /home/ovms/combine_models.py

# Switch to the existing user
USER 1000
ENV PATH="/home/user/.venv/bin:$PATH"

# Install UV requirements
WORKDIR /home/user/
COPY ./docker/pyproject.toml pyproject.toml
COPY ./docker/uv.lock uv.lock
RUN uv sync --locked --no-cache

# Copy OpenVINO Tokenizers library to the correct location
RUN cp /ovms/lib/libopenvino_tokenizers.so /home/user/.venv/lib/python3.12/site-packages/openvino_tokenizers/lib/libopenvino_tokenizers.so
RUN chmod 644 /home/user/.venv/lib/python3.12/site-packages/openvino_tokenizers/lib/libopenvino_tokenizers.so
RUN chown -R 1000:1000 /home/user/.venv

# Set the working directory and entrypoint
WORKDIR /home/ovms/
ENTRYPOINT ["./entrypoint.sh"]