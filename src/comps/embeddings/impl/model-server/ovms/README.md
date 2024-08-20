# OVMS Model Server

This folder contains the scripts to run an embedding model with OVMS.

## Overview

OVMS is an open-source model server that provides a scalable and efficient solution for deploying deep learning models in production environments. It is built on top of the OpenVINO™ toolkit, which enables optimized inference across a wide range of hardware platforms.

## Getting Started

To get started with OVMS, install all required libraries, specify `MODEL_NAME` in `run_ovms.sh` and run the script.
```bash
pip3 install -r https://raw.githubusercontent.com/openvinotoolkit/model_server/releases/2024/3/demos/continuous_batching/requirements.txt
chmod +x run_ovms.sh
./run_ovms.sh
```

## Health check
If you'd like to check whether the endpoint is already running, check out following request:
```bash
export OVMS_MODEL_NAME="bge-large-en-v1.5"
curl http://localhost:9001/v2/models/${OVMS_MODEL_NAME}
```

If the endpoint is correctly running, it should print out an output similar to the one below:
```json
{
   "name":"bge-large-en-v1.5",
   "versions":["1"],
   "platform":"OpenVINO",
   "inputs":[
      {
         "name":"Parameter_1",
         "datatype":"BYTES",
         "shape":[-1]
      }
   ],
   "outputs":[
      {
         "name":"last_hidden_state",
         "datatype":"FP32",
         "shape":[-1,-1,1024]
      }
   ]
}
```

## Example Request
Example request will look as follows:
```bash
curl -X POST http://localhost:9001/v2/models/${OVMS_MODEL_NAME}/infer -H 'Content-Type: application/json' -d '{"inputs" : [ {"name" : "Parameter_1", "shape" : [1], "datatype"  : "BYTES", "data" : ["What is Intel Gaudi?"]}]}'
```

For detailed instructions and examples, please refer to the [documentation](https://github.com/openvinotoolkit/model_server/blob/main/docs/home.md).