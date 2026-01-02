#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import logging
from datetime import datetime
import json
import os

import urllib3
import yaml

from pathlib import Path
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

from comps import (
    change_opea_logger_level,
    get_opea_logger
)

# Disable SSL warnings for unverified HTTPS requests
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from tests.e2e.evals.evaluation.rag_eval import Evaluator
from tests.e2e.evals.metrics.ragas import RagasMetric
from tests.e2e.validation.buildcfg import cfg

logger = get_opea_logger("RAG Evaluator Multihop")
change_opea_logger_level(logger, log_level=os.getenv("OPEA_LOGGER_LEVEL", "INFO"))
logging.getLogger("httpcore").setLevel(logging.ERROR) #disabling mass loging for http requests


class MultiHop_Evaluator(Evaluator):

    def get_ground_truth_text(self, data: dict):
        return data["answer"]

    def get_query(self, data: dict):
        return data["query"]

    def get_question_type(self, data: dict):
        return data.get("question_type") or "unknown"

    def get_template(self):
        return None

    def get_golden_context(self, data):
        return [each["fact"] for each in data["evidence_list"]]

    def evaluate(self, all_queries, arguments):
        if arguments.resume_checkpoint:
            logger.warning("Resuming evaluation is not supported for text generation metrics. Evaluation will proceed from the initial state.")

        if arguments.keep_checkpoint:
            logger.warning("Keep checkpoint option is not supported for text generation metrics. Evaluation will proceed without saving intermediate results.")

        results = []
        index = 0

        for data in tqdm(all_queries):
            query = self.get_query(data)

            generated_text = self.send_request(query, arguments)
            data["generated_text"] = generated_text

            result = {"id": index, "uuid": self.get_uuid(query), "question_type": self.get_question_type(data), **self.scoring(data)}
            logger.debug(f"Result for query {index}: {result}")
            results.append(result)
            index += 1

        valid_results = self.remove_invalid(results)

        try:
            overall = self.compute_overall_metrics(valid_results) if len(valid_results) > 0 else {}
        except Exception as e:
            print(repr(e))
            overall = dict()

        output = {"overall": overall, "results": results}

        try:
            self.save_output(output)
        except Exception as e:
            logger.error(f"Failed to save output: {e}")

        return output 

    def set_checkpoint(self, checkpoint_file: str):
        # change output path to append results
        self.output_checkpoint_file = checkpoint_file

    def cleanup(self):
        try:
            os.remove(self.output_checkpoint_file)
        except Exception as e:
            logger.warning(f"Failed to remove checkpoint file {self.output_checkpoint_file}: {e}")

    def read_output(self, checkpoint_file: str) -> list[dict]:
        try:

            # load results from previous checkpoint
            results = self.load_jsonl(checkpoint_file)
            results = self.remove_invalid(results)
            # change output path to append results, use this name of resume
            self.set_checkpoint(checkpoint_file)

            return results

        except FileNotFoundError as e:
            logger.error(f"Resume file not found: {checkpoint_file} not found, error= {str(e)}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON from resume file {checkpoint_file}, err={str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while reading resume file {checkpoint_file}: {str(e)}")
            raise

    def resume(self, checkpoint_file: str):
        logger.info(f"Resuming evaluation from checkpoint file: {checkpoint_file}")
        results = self.read_output(checkpoint_file)
        return results

    def get_retrieval_metrics(self, all_queries, arguments):
        keep_checkpoint = arguments.keep_checkpoint

        results = []
        index = 0
        saved_uuids = []

        # resume evaluation
        if arguments.resume_checkpoint:
            try:
                checkpoint_file = arguments.resume_checkpoint
                results = self.resume(checkpoint_file)
                saved_uuids = [result["uuid"] for result in results]

                logger.info(
                    f"Resuming evaluation from file '{checkpoint_file}': "
                    f"completed {len(saved_uuids)} queries, "
                    f"remaining {len(all_queries) - len(saved_uuids)} queries."
                )

            except Exception as e:
                logger.error(f"Failed to resume evaluation using {checkpoint_file}: {str(e)}")
                return {}


        index = len(results)  # Start from the next index after the last saved result
        logger.info(f"Writing partial results to checkpoint file: {self.output_checkpoint_file}")

        # TODO: call retrieval and scoring in parallel
        for data in tqdm(all_queries):
            query = self.get_query(data)
            uuid = self.get_uuid(query)
            if uuid in saved_uuids:
                logger.info(f"Skipping query with UUID {uuid} as it has already been evaluated.")
                continue  # Skip results that have already been evaluated and are valid

            logger.info(f"Processing query: '{query}'")
            result = {"id": index, "uuid": uuid, **self.scoring_retrieval(data, normalize=not arguments.skip_normalize)}
            logger.debug(f"Result for query {index} {query}: {result}")
            results.append(result)
            index += 1

            # save partial results to output file
            self.append_jsonl(result)


        if len(results) == 0:
            logger.warning("No queries processed, returning empty metrics.")
            return {}

        try:
            # Calculate average metrics over all queries
            overall = self.compute_overall_retrieval_metrics(results) if len(results) > 0 else {}
        except Exception as e:
            logger.error(f"Error computing overall retrieval metrics: {e}")
            overall = dict()

        output = {"overall": overall, "results": results}
        logger.info(f"Evaluation completed. Total queries processed: {len(results)}")
        try:
            self.save_output(output)
        except Exception as e:
            logger.error(f"Failed to save output: {e}")
            keep_checkpoint = True  # override to preserve checkpoint if saving fails

        # cleanup checkpoint file if not keeping it
        if not keep_checkpoint:
            self.cleanup()

        return output

    def prepare_ragas_record(self, data, arguments):
        query = self.get_query(data)
        question_type = self.get_question_type(data)
        generated_text = self.send_request(query, arguments)

        try:
            retrieved_documents = self.get_reranked_documents(query)
        except (ConnectionError, ValueError) as e:
            logger.error(f"Failed to retrieve documents for RAGAS evaluation on query '{query}': {e}")
            raise

        return {
            "query": query,
            "question_type": question_type,
            "generated_text": generated_text,
            "ground_truth": self.get_ground_truth_text(data),
            "golden_context": self.get_golden_context(data),
            "retrieved_documents": retrieved_documents
        }

    def _convert_ragas_result_to_dict(self, ragas_metrics):
        """
        Convert RAGAS EvaluationResult to a plain dictionary for JSON serialization.

        Args:
            ragas_metrics: RAGAS EvaluationResult object

        Returns:
            dict: Dictionary with metric names as keys and float values
        """
        # Use the internal _repr_dict which has already computed the mean values
        if hasattr(ragas_metrics, '_repr_dict'):
            return dict(ragas_metrics._repr_dict)

        # Fallback to manual extraction if _repr_dict is not available
        ragas_metrics_dict = {}
        ragas_metric_names = ['answer_correctness', 'answer_relevancy', 'semantic_similarity',
                       'context_precision', 'context_recall', 'faithfulness']

        for metric_name in ragas_metric_names:
            try:
                if hasattr(ragas_metrics, metric_name):
                    value = getattr(ragas_metrics, metric_name)
                    ragas_metrics_dict[metric_name] = float(value)
                elif metric_name in ragas_metrics:
                    value = ragas_metrics[metric_name]
                    ragas_metrics_dict[metric_name] = float(value)
            except (TypeError, ValueError) as e:
                logger.warning(f"Could not convert metric '{metric_name}' to float: {e}. Skipping.")

        return ragas_metrics_dict

    # TODO: Explore if it's possible to make the results more traceable (e.g., results per query)
    # Add saving results to the output file
    def get_ragas_metrics(self, all_queries, arguments):
        # todo: no option to resume - all ragas_input are passed to metric.measure
        if arguments.resume_checkpoint:
            logger.warning("Resuming evaluation is not supported for RAGAS metrics. Evaluation will proceed from the initial state.")

        if arguments.keep_checkpoint:
            logger.warning("Keep checkpoint option is not supported for RAGAS metrics.")


        from langchain_huggingface import HuggingFaceEndpointEmbeddings
        try:
            embeddings = HuggingFaceEndpointEmbeddings(model=arguments.embedding_endpoint)
            embeddings.embed_query("test")  # Test the embeddings service
            logger.info(f"Successfully connected to embeddings endpoint: {arguments.embedding_endpoint}")
        except Exception as e:
            logger.error(f"Failed to connected to embeddings endpoint: {e}")
            raise e

        try:
            metric = RagasMetric(threshold=0.5, model=arguments.llm_judge_endpoint, embeddings=embeddings, use_vllm=True, model_name="meta-llama/Llama-3.1-8B-Instruct")
        except Exception as e:
            logger.error(f"Failed to initialize RagasMetric: {e}")
            raise e

        ragas_inputs = {
            "question": [],
            "answer": [],
            "ground_truth": [],
            "contexts": [],
        }

        # Keep track of query metadata for results
        query_metadata = []

        # Use ThreadPoolExecutor to parallelize the preparation of Ragas records
        # TODO: max_workers=1 as keycloak handler does not handle multithreading properly
        with ThreadPoolExecutor(max_workers=1) as executor:
            futures = [executor.submit(self.prepare_ragas_record, data, arguments) for data in all_queries]

            for future in tqdm(as_completed(futures), total=len(futures)):
                result = future.result()

                ragas_inputs["question"].append(result["query"])
                ragas_inputs["answer"].append(result["generated_text"])
                ragas_inputs["ground_truth"].append(result["ground_truth"])
                ragas_inputs["contexts"].append(result["retrieved_documents"])

                # Store metadata for each query
                query_metadata.append({
                    "uuid": self.get_uuid(result["query"]),
                    "query": result["query"],
                    "question_type": result["question_type"],
                    "generated_text": result["generated_text"],
                    "ground_truth": result["ground_truth"],
                    "golden_context": result["golden_context"],
                    "num_reranked_documents": len(result["retrieved_documents"]),
                    "reranked_documents": result["retrieved_documents"]
                })


        try:
            ragas_metrics = metric.measure(ragas_inputs)
            logger.info(f"Ragas metrics computed successfully: {ragas_metrics}")

        except Exception as e:
            logger.error(f"Failed to compute Ragas metrics: {e}")
            raise e

        try:
            # Convert EvaluationResult to dict for JSON serialization
            ragas_metrics_dict = self._convert_ragas_result_to_dict(ragas_metrics)

            # Add num field to overall metrics
            ragas_metrics_dict["num"] = len(ragas_inputs["question"])

            # Extract per-query results and enrich with metadata
            per_query_results = []
            if hasattr(ragas_metrics, 'scores'):
                for idx, score in enumerate(ragas_metrics.scores):
                    enriched_result = {
                        "id": idx,
                        "uuid": query_metadata[idx]["uuid"],
                        "ragas_metrics": score,
                        "log": {
                            "query": query_metadata[idx]["query"],
                            "question_type": query_metadata[idx]["question_type"],
                            "generated_text": query_metadata[idx]["generated_text"],
                            "ground_truth": query_metadata[idx]["ground_truth"],
                            "golden_context": query_metadata[idx]["golden_context"],
                            "num_reranked_documents": query_metadata[idx]["num_reranked_documents"],
                            "reranked_documents": query_metadata[idx]["reranked_documents"],
                            "evaluateDatetime": str(datetime.now()),
                        },
                        "valid": query_metadata[idx]["generated_text"] is not None and len(query_metadata[idx]["generated_text"].strip()) != 0
                    }
                    per_query_results.append(enriched_result)

            output = {"overall": ragas_metrics_dict, "results": per_query_results}
            self.save_output(output)

        except Exception as e:
            logger.error(f"Failed to save output: {e}")

        return ragas_metrics


""" Validate cluster configuration file if exists"""
def validate_config_files_exists(args):
    if args.auth_file:
        auth_path = Path(args.auth_file)
        if not auth_path.exists():
            logger.error(f"Auth file does not exist: {args.auth_file}")
            raise FileNotFoundError(f"Auth file not found: {args.auth_file}")

    if args.cluster_config_file:
        config_path = Path(args.cluster_config_file)
        if not config_path.exists():
            logger.error(f"Cluster config file does not exist: {args.cluster_config_file}")
            raise FileNotFoundError(f"Cluster config not found: {args.cluster_config_file}")


""" Load cluster configuration from file into singleton dict (cfg) - cluster information (FQDN, pipeline, proxies, etc.)"""
def load_cluster_configuration_file(args):
    build_config_filepath = args.cluster_config_file
    if os.path.exists(build_config_filepath):
        logger.debug(f"Loading build configuration from {build_config_filepath}")
        with open(build_config_filepath, "r") as f:
            build_configuration = yaml.safe_load(f)
        cfg.update(build_configuration)
    else:
        logger.warning(f"Build configuration file {build_config_filepath} does not exist. Using default configuration.")
    return cfg


def get_project_root():
    pythonpath = os.getenv("PYTHONPATH")
    if not pythonpath:
        logger.error("PYTHONPATH not set, please set PYTHONPATH")
        raise EnvironmentError("PYTHONPATH not set")
    project_root = pythonpath.split(os.pathsep)[0]
    return project_root


def args_parser():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--dataset_path", default="multihop_dataset/MultiHopRAG.json", help="Path to the dataset")
    parser.add_argument("--docs_path", default="multihop_dataset/corpus.json", help="Path to the retrieval documents")
    parser.add_argument("--output_dir", type=str, default="./output", help="Directory to save evaluation results")
    parser.add_argument("--ingest_docs", action="store_true", help="Whether to ingest documents to vector database")
    parser.add_argument("--generation_metrics", action="store_true", help="Whether to compute text generation metrics such as BLEU and ROUGE")
    parser.add_argument("--retrieval_metrics", action="store_true", help="Whether to compute retrieval metrics such as Hits, MAP and MRR")
    parser.add_argument("--ragas_metrics", action="store_true", help="Whether to compute ragas metrics such as answer correctness, relevancy, semantic similarity, context precision, context recall , and faithfulness")
    parser.add_argument("--skip_normalize", action="store_true", help="Skip normalization of 'None' separators in retrieval metrics. By default, normalization is enabled")
    parser.add_argument("--limits", type=int, default=100, help="Number of queries to evaluate. Set to 0 to evaluate all provided queries")
    parser.add_argument("--exclude_types", type=str, nargs='+', dest='exclude_types', help="Exclude queries by question type. Queries matching these question types will be skipped. Example: --exclude_types comparision_query")
    parser.add_argument("--resume_checkpoint", type=str, help="Path to a checkpoint file to resume evaluation from previously saved progress")
    parser.add_argument("--keep_checkpoint", action="store_true", help="Keep the checkpoint file after successful evaluation instead of deleting it")
    parser.add_argument("--llm_judge_endpoint", type=str, default="http://localhost:8008", help="URL of the LLM judge service. Only used for RAGAS metrics")
    parser.add_argument("--embedding_endpoint", type=str, default="http://localhost:8090/embed", help="URL of the embedding service endpoint. Only used for RAGAS metrics")
    parser.add_argument("--temperature", type=float, help="Controls the randomness of the model's text generation. Defaults to RAG system setting if omitted")
    parser.add_argument("--max_new_tokens", type=int, help="Maximum number of new tokens to be generated by the model. Defaults to RAG system setting if omitted")
    parser.add_argument("--auth_file", type=str, default=os.path.abspath(os.path.join(get_project_root(), "..", "deployment/ansible-logs/default_credentials.txt")), help="Path to auth file")
    parser.add_argument("--cluster_config_file", type=str, default=os.path.abspath(os.path.join(get_project_root(), "..", "deployment/inventory/sample/config.yaml")), help="Path to cluster configuration file")
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


def filter_queries_by_type(queries, exclude_types=None):
    """
    Filter queries by excluding specific question types.

    Args:
        queries: List of query dictionaries
        exclude_types: List of question types to exclude (if None, exclude none)

    Returns:
        Filtered list of queries
    """
    if not exclude_types:
        return queries

    logger.info(f"Excluding question types: {exclude_types}")
    # Normalize exclude_types to lowercase and strip whitespace for case-insensitive comparison
    normalized_exclude_types = {qt.lower().strip() for qt in exclude_types}
    filtered = [q for q in queries if q.get("question_type", "").lower().strip() not in normalized_exclude_types]

    return filtered


def main():
    args = args_parser()
    logger.info(f"Running Multihop evaluation with arguments: {args.__dict__}")
    os.makedirs(args.output_dir, exist_ok=True)

    # Initialize the evaluator
    validate_config_files_exists(args)
    load_cluster_configuration_file(args)
    evaluator = MultiHop_Evaluator(output_dir=args.output_dir,
                                   auth_file=args.auth_file)

    try:
        evaluator.validate_connections_to_rag_services()
        evaluator.fetch_system_args()  # Fetch RAG system configuration
    except Exception as e:
        logger.error(f"Failed to connect to RAG, err={e}")
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

        # Filter by question type if specified
        if args.exclude_types:
            all_queries = filter_queries_by_type(all_queries, args.exclude_types)
            logger.info(f"Queries after type filtering: {len(all_queries)}")

    except Exception as e:
        logger.error(f"Error filtering queries: {e}")

    if not all_queries:
        logger.error("No queries remain after filtering 'null_query' category. Please check the dataset.")
        return

    if args.limits > 0 and args.limits < len(all_queries):
        all_queries = all_queries[:args.limits]
        logger.info(f"Limit applied. Using the first {args.limits} queries for evaluation")


    if not (args.generation_metrics or args.ragas_metrics or args.retrieval_metrics):
        logger.warning("Skipping evaluation: no metrics selected. Use --generation_metrics, --ragas_metrics, or --retrieval_metrics to enable evaluation")
        return

    # todo: optimize the code to process callculation BLUE, ROUGE metrics and RAGAS metrics in one pass
    if args.generation_metrics:
        logger.info("Starting evaluation of text generation metrics...")
        results = evaluator.evaluate(all_queries, args)
        logger.info(f"Evaluation text generation overall: {results['overall']}")

    if args.ragas_metrics:
        logger.info("Starting evaluation of RAGAS metrics...")
        ragas_metrics = evaluator.get_ragas_metrics(all_queries, args)
        logger.info(f"Ragas metrics: {ragas_metrics}")
        # todo: save it

    if args.retrieval_metrics:
        logger.info("Starting evaluation of retrieval metrics...")
        retrieval_metrics = evaluator.get_retrieval_metrics(all_queries, args)
        logger.info(f"Retrieval metrics: {retrieval_metrics.get('overall', {})}")



if __name__ == "__main__":
    main()
