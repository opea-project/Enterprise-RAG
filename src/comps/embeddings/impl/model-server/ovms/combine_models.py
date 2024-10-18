# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

import openvino as ov
from openvino_tokenizers import connect_models

"""
This script combines an embedding model and a tokenizer model using OpenVINO and saves the combined model.

Usage:
    Set the following environment variables before running the script:
        EMBEDDING_DIR: Directory containing the embedding model files.
        TOKENIZER_DIR: Directory containing the tokenizer model files.
        OUTPUT_DIR (optional): Directory where the combined model will be saved. Defaults to '/model/1'.

Example usage:
    export EMBEDDING_DIR=/data/bge-large-en-v1.5_embeddings
    export TOKENIZER_DIR=/data/bge-large-en-v1.5_tokenizer
    export OUTPUT_DIR=/model/1
    python combine_models.py
"""

def combine_models(embedding_dir, tokenizer_dir, output_dir):
    core = ov.Core()
    embedding_model = core.read_model(model=os.path.join(embedding_dir, "openvino_model.xml"))
    tokenizer_model = core.read_model(model=os.path.join(tokenizer_dir, "openvino_tokenizer.xml"))
    combined_model = connect_models(tokenizer_model, embedding_model)

    ov.save_model(combined_model, os.path.join(output_dir, "model.xml"))

def validate_directory(path):
    if not os.path.isdir(path):
        raise ValueError(f"Invalid directory: {path}")
    return os.path.abspath(os.path.normpath(path))

def validate_output_directory(path):
    path = os.path.abspath(os.path.normpath(path))
    if not os.path.isdir(path):
        os.makedirs(path)
    return path


if __name__ == "__main__":

    embedding_dir = validate_directory(str(os.getenv('EMBEDDING_DIR')))
    tokenizer_dir = validate_directory(str(os.getenv('TOKENIZER_DIR')))
    output_dir = validate_output_directory(str(os.getenv('OUTPUT_DIR', default='/model/1')))

    combine_models(embedding_dir, tokenizer_dir, output_dir)

