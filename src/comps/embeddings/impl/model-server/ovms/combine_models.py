# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
from openvino import compile_model
from openvino_tokenizers import connect_models
import openvino as ov
import sys
import os

if __name__ == "__main__":
    embedding_dir = sys.argv[1]
    tokenizer_dir = sys.argv[2]
    output_dir = embedding_dir.rsplit("/", 1)[0]
    model_name = embedding_dir.split("/")[-1].rsplit("_", 1)[0]

    core = ov.Core()
    embedding_model = core.read_model(model=os.path.join(embedding_dir, "openvino_model.xml"))
    embedding_model_compiled = core.compile_model(model=embedding_model, device_name="CPU")

    tokenizer_model = core.read_model(model=os.path.join(tokenizer_dir, "openvino_tokenizer.xml"))
    tokenizer_model_compiled = core.compile_model(model=tokenizer_model, device_name="CPU")

    combined_model = connect_models(tokenizer_model, embedding_model)
    compiled_combined_model = compile_model(combined_model)

    ov.save_model(combined_model, os.path.join(output_dir, f"{model_name}_combined/model.xml"))
