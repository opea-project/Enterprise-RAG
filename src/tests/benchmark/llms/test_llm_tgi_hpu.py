# ruff: noqa: E711, E712
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
# To run this test with pytest, run the following command:
# pytest -s --benchmark-min-rounds=20 --benchmark-group-by=param:max_new_tokens benchmark/llms/

import pytest
import requests
import subprocess # nosec B404

from pathlib import Path

HF_TOKEN = ""
TGI_PATH = "../comps/llms/impl/model_server/tgi/docker"
FP8_DOCKER_COMPOSE_NAME = "docker-compose-hpu-fp8.yaml"
BF16_DOCKER_COMPOSE_NAME = "docker-compose-hpu.yaml"
TGI_SCRIPT = "run_tgi.sh"

FP8_LLM_TGI_PORT=8008
FP8_HABANA_VISIBLE_DEVICES="0"
BF16_LLM_TGI_PORT=8009
BF16_HABANA_VISIBLE_DEVICES="1"

# ATTENTION: Test need to have access to already quantized models
FP8_PATH = "../fp8_quantization/data/"

def send_request(port, max_new_tokens, session):
    url = f"http://0.0.0.0:{port}/generate"
    headers = {
        "Content-Type": "application/json"
    }
    data = f'{{"inputs":"What is Deep Learning?","parameters":{{"max_new_tokens":{max_new_tokens}, "do_sample": true}}}}'
    response = session.post(url, data=data, headers=headers, timeout=300)

    assert response.ok == True
    assert response.status_code == 200
    assert "generated_text" in response.json()

@pytest.fixture(scope="function")
def session():
    session = requests.Session()
    yield session
    session.close()

@pytest.mark.usefixtures("benchmark", "session")
@pytest.mark.parametrize("max_new_tokens", [32, 64, 128, 512, 1024])
class TestLLMTGIDatatypes:
    @pytest.fixture(scope="class", params=[("meta-llama/Llama-2-7b-hf", 1, 1)])
    def init_tgi(self, request):
        model_name, batch_size, num_shard = request.param

        cur_fp8_path = Path(FP8_PATH).joinpath(model_name).joinpath(f"bs_{batch_size}_shards_{num_shard}")
        if_sharded = "true" if num_shard > 1 else "false"

        # Run FP8 TGI
        p = subprocess.Popen(["docker", "compose", "--env-file=.env.hpu", "-f", FP8_DOCKER_COMPOSE_NAME, "up", "--build", "llm-tgi-fp8-model-server"],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                env={"LLM_DEVICE": "hpu",
                                    "LLM_TGI_PORT": str(FP8_LLM_TGI_PORT),
                                    "LLM_TGI_MODEL_NAME": model_name,
                                    "FP8_QUANTIZE_MODEL_PATH": cur_fp8_path,
                                    "HABANA_VISIBLE_DEVICES": FP8_HABANA_VISIBLE_DEVICES,
                                    "SHARDED": if_sharded,
                                    "NUM_SHARD": str(num_shard),
                                    "BATCH_SIZE": str(batch_size),
                                    "HF_TOKEN": HF_TOKEN
                                    },
                                cwd=TGI_PATH,
                                shell=False) # nosec B603

        all_good = False
        for line in iter(p.stdout.readline, b''):
            line = line.decode('utf-8').strip()
            print(line)
            if "text_generation_router" in line and "Connected" in line:
                all_good = True
                break
        p.stdout.close()
        if not all_good:
            raise Exception("Failed to start TGI server")

        # Run BF16 TGI
        p = subprocess.Popen(["docker", "compose", "--env-file=.env.hpu", "-f", BF16_DOCKER_COMPOSE_NAME, "up", "--build", "llm-tgi-model-server"],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                env={"LLM_DEVICE": "hpu",
                                    "LLM_TGI_PORT": str(BF16_LLM_TGI_PORT),
                                    "LLM_TGI_MODEL_NAME": model_name,
                                    "HABANA_VISIBLE_DEVICES": BF16_HABANA_VISIBLE_DEVICES,
                                    "SHARDED": if_sharded,
                                    "NUM_SHARD": str(num_shard),
                                    "BATCH_SIZE": str(batch_size),
                                    "HF_TOKEN": HF_TOKEN
                                    },
                                cwd=TGI_PATH,
                                shell=False) # nosec B603

        all_good = False
        for line in iter(p.stdout.readline, b''):
            line = line.decode('utf-8').strip()
            print(line)
            if "text_generation_router" in line and "Connected" in line:
                all_good = True
                break
        p.stdout.close()
        if not all_good:
            raise Exception("Failed to start TGI server")

        yield

        # Stop the servers
        p = subprocess.Popen(["docker", "compose", "-f", Path.cwd().joinpath(TGI_PATH).joinpath(BF16_DOCKER_COMPOSE_NAME), "down"],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                cwd=TGI_PATH,
                                shell=False) # nosec B603, B607

        for line in iter(p.stdout.readline, b''):
            line = line.decode('utf-8').strip()
            print(line)
        p.stdout.close()

        p = subprocess.Popen(["docker", "compose", "-f", Path.cwd().joinpath(TGI_PATH).joinpath(FP8_DOCKER_COMPOSE_NAME), "down"],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                cwd=TGI_PATH,
                                shell=False) # nosec B603, B607

        for line in iter(p.stdout.readline, b''):
            line = line.decode('utf-8').strip()
            print(line)
        p.stdout.close()

    def test_llm_tgi_hpu_fp8(self, max_new_tokens: int, init_tgi, session, benchmark) -> None:
        benchmark(send_request, FP8_LLM_TGI_PORT, max_new_tokens, session)

    def test_llm_tgi_hpu_bf16(self, max_new_tokens: int, init_tgi, session, benchmark) -> None:
        benchmark(send_request, BF16_LLM_TGI_PORT, max_new_tokens, session)
