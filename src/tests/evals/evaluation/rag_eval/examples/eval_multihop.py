#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import json
import os
from datetime import datetime

from tqdm import tqdm

from comps import (
    change_opea_logger_level,
    get_opea_logger
)

from tests.evals.evaluation.rag_eval import Evaluator

logger = get_opea_logger("RAG Evaluator Multihop")
change_opea_logger_level(logger, log_level=os.getenv("OPEA_LOGGER_LEVEL", "INFO"))


class MultiHop_Evaluator(Evaluator):
  
    def get_ground_truth_text(self, data: dict):
        return data["answer"]

    def get_query(self, data: dict):
        return data["query"]

    def get_template(self):
        return None

    def evaluate(self, all_queries, arguments):
        results = []
        accuracy = 0
        index = 0

        for data in tqdm(all_queries):
            query = self.get_query(data)
            generated_text = self.send_request(query, arguments)
            data["generated_text"] = generated_text
            
            # same method with paper: https://github.com/yixuantt/MultiHop-RAG/issues/8
            if data["answer"] in generated_text:
                accuracy += 1
            result = {"id": index, **self.scoring(data)}

            logger.debug(f"Result for query {index}: {result}")
            results.append(result)

            index += 1

        valid_results = self.remove_invalid(results)

        try:
            overall = self.compute_overall(valid_results) if len(valid_results) > 0 else {}
        except Exception as e:
            print(repr(e))
            overall = dict()

        overall.update({"accuracy": accuracy / len(results)})

        output = {"overall": overall, "results": results}

        try:
            self.save_output(output)
        except Exception as e:
            logger.error(f"Failed to save output: {e}")

        return output 


def args_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset_path", default="multihop_dataset/MultiHopRAG.json", help="Path to the dataset")
    parser.add_argument("--docs_path", default="multihop_dataset/corpus.json", help="Path to the retrieval documents")
    parser.add_argument("--output_dir", type=str, default="./output", help="Directory to save evaluation results")
    parser.add_argument(
        "--temperature", type=float, default=0.1, help="Controls the randomness of the model's text generation"
    )
    parser.add_argument("--ingest_docs", action="store_true", help="Whether to ingest documents to vector database")
    parser.add_argument("--retrieval_metrics", action="store_true", help="Whether to compute retrieval metrics")
    parser.add_argument("--ragas_metrics", action="store_true", help="Whether to compute ragas metrics")
    parser.add_argument("--limits", type=int, default=100, help="Number of examples to be evaluated")

    args = parser.parse_args()
    return args


def download_dataset(filepath: str) -> None:
    from huggingface_hub import hf_hub_download

    dirname = os.path.dirname(filepath)
    filename = os.path.basename(filepath)

    try:
        hf_hub_download(repo_id="yixuantt/MultiHopRAG",
                         repo_type="dataset",
                         filename=filename,
                         local_dir=dirname)
        logger.info(f"Dataset downloaded successfully to {filepath}")
    except Exception as e:
        logger.error(f"Failed to download dataset: {e}")
        raise e
    

def load_or_download(filepath):
    if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
        logger.info(f"File {filepath} is missing or empty. Downloading dataset...")
        download_dataset(filepath)

    try:
        with open(filepath, "r") as file:
            logger.info(f"Reading data from: {filepath}")
            data = json.load(file)

    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {filepath}: {e}")
        return None

    except FileNotFoundError as e:
        logger.error(f"File {filepath} not found: {e}")
        return None

    except Exception as e:
        logger.error(f"Error reading file {filepath}: {str(e)}")
        return None

    return data

def filter_category_null_queries(queries):
    """
    Remove queries with question type 'null_query' from the list.

    Args:
        queries (list of dict): List of queries, each query is expected
                                to have a 'question_type' key.

    Returns:
        list of dict: Filtered list excluding queries where 'question_type' is 'null_query'.

    Note:
        Queries labeled as 'null_query' indicate cases where there is insufficient
        information in the available documents to answer the question.
        These queries typically expect the answer "Insufficient information"
        and are excluded from evaluation to focus on answerable queries.

    Example:
        A query like "What is the capital of country X?" where no information
        about country X exists in the dataset would be labeled as 'null_query'.
    """

    return [q for q in queries if q.get("question_type") != 'null_query']

def main():
    args = args_parser()
    logger.info(f"Running Multihop evaluation with arguments: {args.__dict__}")
    os.makedirs(args.output_dir, exist_ok=True)
    current_time = datetime.now().strftime("%Y%m%d%H%M%S")
    output_save_path = os.path.join(args.output_dir, f"multihop_{current_time}.json")

    # Initialize the evaluator
    evaluator = MultiHop_Evaluator(output_path=output_save_path)

    try:
        evaluator.validate_connections_to_rag_services()
    except Exception as e:
        logger.error(f"Connection check to RAG services failed: {e}")
        return

    documents = []
    doc_data = load_or_download(args.docs_path)  
    if doc_data is None:
        logger.error(f"Failed to load Multihop RAG documents corpus from {args.docs_path}.")
        return
    
    for doc in doc_data:
        # NOTE: nothing happens with metadata, just body is used in the GenAIEval code
        # metadata = {"title": doc["title"], "published_at": doc["published_at"], "source": doc["source"]}
        documents.append(doc["body"])

    logger.info(f"Total corpus documents: {len(documents)}")

    if args.ingest_docs:
        tmp_corpus_file = "tmp_corpus.txt"
        with open(tmp_corpus_file, "w") as f:
            for doc in documents:
                f.write(doc + "\n")

        try:
            evaluator.ingest_docs(tmp_corpus_file)
        except Exception as e:
            logger.error(f"Error during file upload: {str(e)}")
            logger.error("Please check the following steps:\n" +
            "1. If this is a new installation, log in via the website, go to the admin panel → ingestion, and try uploading sample documents.\n" +
            "2. If you are using a proxy, ensure your no_proxy environment variable includes 'erag.com' and 's3.erag.com'.\n" +
            f"3. If the problem persists, upload the file {tmp_corpus_file} (located in the current directory) manually through the web UI and rerun the evaluation without the --ingest_docs flag."
            )
            return

    all_queries = load_or_download(args.dataset_path)  # Load documents corpus
    if all_queries is None:
        logger.error(f"Failed to load queries from {args.dataset_path}")
        return

    logger.info(f"Total queries in dataset: {len(all_queries)}")

    try:
        # skip queries marked as "null_query"
        logger.info("Filtering queries categorized as 'null_query' (insufficient information)...")
        all_queries = filter_category_null_queries(all_queries)
        logger.info(f"Queries remaining: {len(all_queries)}")

    except Exception as e:
        logger.error(f"Error filtering queries categorized as 'null_query': {e}")

    if not all_queries:
        logger.error("No queries remain after filtering 'null_query' category. Please check the dataset.")
        return

    if args.limits > 0 and args.limits < len(all_queries):
        all_queries = all_queries[:args.limits]
        logger.info(f"Limit applied. Using the first {args.limits} queries for evaluation")

    # Evaluate the queries
    results = evaluator.evaluate(all_queries, args)
    logger.info(f"Evaluation overall: {results['overall']}")

    if args.ragas_metrics:
        logger.warning("Ragas metrics are not implemented for MultiHop evaluation yet.")

    if args.retrieval_metrics:
        logger.warning("Retrieval metrics are not implemented for MultiHop evaluation yet.")


if __name__ == "__main__":
    main()
