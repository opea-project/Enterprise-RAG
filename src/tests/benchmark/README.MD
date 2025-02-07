### Supported benchmarking

- Gaudi
  - VLLM
  - Microservice using VLLM

- SPR
  - VLLM
  - Microservice using VLLM

### Prepare environment

Before start, ensure you have `HF_TOKEN` in your `env`. The token will be further passed to containers
to pull AI models.
```bash
$ echo ${HF_TOKEN}
abcdefghi1234567890 
```

Additionally, prepare Python virtual environment and install deps. The simplest way is:
```bash
$ pwd
.../src/tests/benchmark

$ python3 -m venv venv
$ source venv/bin/activate
(venv) $ pip install -U pip
(venv) $ pip install -r ../microservices/requirements.txt
```

### Configure benchmark
As of now, go to _/src/tests/benchmark/config_defaults/benchmark_name.yaml_
and adjust file for your needs.

### How to run

Set `PYTHONPATH` into repository root either in your shell or along with run command.

```bash
$ pwd
.../src/tests/benchmark

(venv) $ PYTHONPATH=/path/to/repository pytest llms/test_vllm_ip_cpu.py
```

### Results

You can find results in /tmp/ directory. Look for files with
**benchmark_results.csv** prefixes with datetime.