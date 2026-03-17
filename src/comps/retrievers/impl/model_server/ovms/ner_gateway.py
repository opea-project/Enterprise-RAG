# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
NER Gateway — KServe v2-compatible API wrapping OVMS token-classification inference.

Handles tokenization (pre), calls OVMS for raw logits, then performs BIO decoding
and entity aggregation (post).  The gateway is designed to run inside the same
container as OVMS, communicating over localhost. 
"""

import json
import logging
import os
from typing import Any, Dict, List

import numpy as np
import requests
from flask import Flask, jsonify, request as flask_request
from scipy.special import softmax
from transformers import AutoTokenizer

# Logging (not using comps logger to avoid dependency)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ner_gateway")

# Gateway core

class NERGateway:
    """KServe v2 gateway wrapping OVMS token-classification inference.

    Pre-processing: tokenize text via HuggingFace AutoTokenizer.
    Post-processing: BIO-decode raw logits and aggregate into entity spans.
    Runs inside the same container as OVMS, communicating over localhost.
    """

    def __init__(
        self,
        ovms_endpoint: str,
        model_name: str,
        hf_model_name: str,
    ):
        self.ovms_url = f"{ovms_endpoint}/v2/models/{model_name}/infer"
        self.model_name = model_name
        self._ovms_timeout = 2.0  # 2 s timeout (localhost, may spike on first call)

        # Load tokenizer (lightweight, no model weights)
        logger.info("Loading tokenizer from %s …", hf_model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(hf_model_name)

        # Load id2label mapping from HuggingFace config.json
        self.id2label = self._load_labels(hf_model_name)
        logger.info(
            "NER Gateway ready: model=%s, labels=%d",
            model_name,
            len(self.id2label),
        )

    # Label loading
    def _load_labels(self, hf_model_name: str) -> Dict[int, str]:
        """Load id2label from HF config.json without model weights."""
        try:
            from huggingface_hub import hf_hub_download

            config_path = hf_hub_download(
                repo_id=hf_model_name, filename="config.json"
            )
            with open(config_path) as fh:
                config = json.load(fh)
            raw = config.get("id2label", {})
            return {int(k): v for k, v in raw.items()}
        except Exception:
            logger.exception("Failed to load id2label; falling back to empty map")
            return {}

    # Inference pipeline
    def infer(self, text: str) -> List[Dict[str, Any]]:
        """text → entities via tokenize → OVMS → BIO-decode → aggregate."""
        # 1. Tokenize
        tokens = self.tokenizer(
            text,
            return_tensors="np",
            return_offsets_mapping=True,
            add_special_tokens=True,
            truncation=True,
            max_length=512,
        )
        input_ids = tokens["input_ids"]  # [1, seq_len]
        attention_mask = tokens["attention_mask"]  # [1, seq_len]
        offsets = tokens["offset_mapping"][0].tolist()  # [[start, end], …]

        # 2. Call OVMS (raw logits)
        payload: Dict[str, Any] = {
            "inputs": [
                {
                    "name": "input_ids",
                    "shape": list(input_ids.shape),
                    "datatype": "INT64",
                    "data": input_ids.flatten().tolist(),
                },
                {
                    "name": "attention_mask",
                    "shape": list(attention_mask.shape),
                    "datatype": "INT64",
                    "data": attention_mask.flatten().tolist(),
                },
            ]
        }

        resp = requests.post(
            self.ovms_url, json=payload, timeout=self._ovms_timeout
        )
        if resp.status_code != 200:
            logger.error("OVMS inference failed: %d %s", resp.status_code, resp.text[:300])
            raise RuntimeError(
                f"OVMS error {resp.status_code}: {resp.text[:300]}"
            )

        # 3. Parse logits from OVMS response
        logits = self._parse_logits(resp.json())  # [1, seq_len, n_labels]

        # 4. BIO decode
        preds = np.argmax(logits[0], axis=-1)  # [seq_len]
        probs = softmax(logits[0], axis=-1)  # [seq_len, n_labels]
        labels = [self.id2label.get(int(p), "O") for p in preds]
        confidences = [float(probs[i, int(p)]) for i, p in enumerate(preds)]

        # 5. Aggregate BIO entities
        return self._aggregate_entities(labels, confidences, offsets, text)

    # OVMS response parsing
    def _parse_logits(self, ovms_resp: Dict) -> np.ndarray:
        """Extract logits tensor from OVMS KServe v2 response."""
        for output in ovms_resp.get("outputs", []):
            if output["name"] == "logits":
                shape = output["shape"]
                data = output["data"]
                return np.array(data, dtype=np.float32).reshape(shape)
        raise ValueError("OVMS response missing 'logits' output")

    # BIO aggregation
    def _aggregate_entities(
        self,
        labels: List[str],
        confidences: List[float],
        offsets: List[List[int]],
        text: str,
    ) -> List[Dict[str, Any]]:
        """Merge BIO-labelled tokens into entity spans.

        Handles the standard BIO case (B- followed by I-) and
        consecutive B-B tokens of the same entity type whose character
        spans are contiguous.
        """
        entities: List[Dict[str, Any]] = []
        cur: Dict[str, Any] | None = None

        for label, conf, (tok_start, tok_end) in zip(
            labels, confidences, offsets
        ):
            # Skip special tokens (offset == (0,0) for [CLS]/[SEP])
            if tok_start == tok_end:
                if cur is not None:
                    entities.append(cur)
                    cur = None
                continue

            if label.startswith("B-"):
                if cur is not None:
                    entities.append(cur)
                cur = {
                    "entity_group": label[2:],
                    "start": tok_start,
                    "end": tok_end,
                    "_confs": [conf],
                }
            elif label.startswith("I-") and cur is not None:
                if label[2:] == cur["entity_group"]:
                    cur["end"] = tok_end
                    cur["_confs"].append(conf)
                else:
                    entities.append(cur)
                    cur = None
            else:
                if cur is not None:
                    entities.append(cur)
                    cur = None

        if cur is not None:
            entities.append(cur)

        # Merge contiguous same-type entities (fixes B-B subword splits).
        entities = self._merge_contiguous_entities(entities, text)

        # Finalise: derive word + avg confidence
        for ent in entities:
            ent["word"] = text[ent["start"]: ent["end"]]
            ent["score"] = round(float(np.mean(ent.pop("_confs"))), 4)
            ent["start"] = int(ent["start"])
            ent["end"] = int(ent["end"])

        return entities

    @staticmethod
    def _merge_contiguous_entities(
        entities: List[Dict[str, Any]], text: str
    ) -> List[Dict[str, Any]]:
        """Merge consecutive entities of the same type with contiguous spans.

        Handles cases where BPE subword tokenization causes a single word
        to be split across multiple B- labelled tokens.
        """
        if not entities:
            return entities

        merged: List[Dict[str, Any]] = [entities[0]]
        for ent in entities[1:]:
            prev = merged[-1]
            gap = text[prev["end"]: ent["start"]]
            if (
                prev["entity_group"] == ent["entity_group"]
                and len(gap) <= 1
                and gap.strip() == ""
            ):
                # Extend the previous entity to cover the new span
                prev["end"] = ent["end"]
                prev["_confs"].extend(ent["_confs"])
            else:
                merged.append(ent)
        return merged


# Flask application
app = Flask(__name__)

# Lazy-initialised singleton
_gateway: NERGateway | None = None


def _get_gateway() -> NERGateway:
    global _gateway
    if _gateway is None:
        ovms_endpoint = os.getenv("OVMS_INTERNAL_ENDPOINT", "http://localhost:9000")
        model_name = os.getenv("NER_MODEL_NAME", "tanaos/tanaos-NER-v1")
        short_name = model_name.rsplit("/", 1)[-1]
        _gateway = NERGateway(ovms_endpoint, short_name, model_name)
    return _gateway


# KServe v2 health / metadata endpoints
@app.route("/v2/health/ready", methods=["GET"])
@app.route("/v2/health/live", methods=["GET"])
def health_check():
    return jsonify({"status": "ready"})

@app.route("/v2/models/<model_name>", methods=["GET"])
@app.route("/v2/models/<model_name>/ready", methods=["GET"])
def model_metadata(model_name: str):
    return jsonify({"name": model_name, "ready": True, "platform": "openvino"})


# KServe v2 inference endpoint
@app.route("/v2/models/<model_name>/infer", methods=["POST"])
def infer_endpoint(model_name: str):
    """Accept KServe v2 input_text, return aggregated entities."""
    try:
        gw = _get_gateway()
        data = flask_request.get_json(force=True)

        # Extract text from inputs
        text = None
        for inp in data.get("inputs", []):
            if inp.get("name") in ("input_text", "text"):
                text_data = inp.get("data", [])
                text = text_data[0] if isinstance(text_data, list) and text_data else text_data
                break

        if not text:
            return jsonify({"error": "No input_text provided"}), 400

        entities = gw.infer(text)

        return jsonify({
            "model_name": model_name,
            "model_version": "1",
            "outputs": [
                {
                    "name": "entities",
                    "datatype": "BYTES",
                    "shape": [len(entities)],
                    "data": entities,
                }
            ],
        })

    except Exception as exc:
        logger.exception("Inference failed")
        return jsonify({"error": str(exc)}), 500


# Entrypoint
if __name__ == "__main__":
    port = int(os.getenv("GATEWAY_PORT", "9001"))
    workers = int(os.getenv("GATEWAY_WORKERS", "2"))
    logger.info("Starting NER Gateway on port %d with %d workers", port, workers)
    # Eager init so startup failures are visible immediately
    _get_gateway()

    import gunicorn.app.base

    class StandaloneApplication(gunicorn.app.base.BaseApplication):
        """Gunicorn wrapper to run Flask app with production WSGI server."""

        def __init__(self, application, options=None):
            self.options = options or {}
            self.application = application
            super().__init__()

        def load_config(self):
            for key, value in self.options.items():
                if key in self.cfg.settings and value is not None:
                    self.cfg.set(key.lower(), value)

        def load(self):
            return self.application

    gunicorn_options = {
        "bind": f"0.0.0.0:{port}",
        "workers": workers,
        "threads": 2,
        "timeout": 30,
        "accesslog": "-",
    }
    StandaloneApplication(app, gunicorn_options).run()
