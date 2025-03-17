# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
from typing import Any
import requests
import base64
import datetime
from dotenv import load_dotenv
from minio.error import S3Error
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from celery import Celery, Task, shared_task
from app.models import FileStatus, LinkStatus
from comps.cores.mega.logger import change_opea_logger_level, get_opea_logger
from app.utils import get_local_minio_client

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), "./.env"))

# Initialize the logger for the microservice
logger = get_opea_logger("edp_microservice")
change_opea_logger_level(logger, log_level=os.getenv("OPEA_LOGGER_LEVEL", "INFO"))

celery = Celery(
    "Celery",
    broker=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.environ.get('CELERY_BACKEND_URL', 'redis://localhost:6379/0'),
    task_ack_late=True,
    taks_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1
)

DATAPREP_ENDPOINT  = os.environ.get('DATAPREP_ENDPOINT')
EMBEDDING_ENDPOINT = os.environ.get('EMBEDDING_ENDPOINT')
INGESTION_ENDPOINT = os.environ.get('INGESTION_ENDPOINT')

class WithEDPTask(Task):
    _db = None
    _minio = None

    def after_return(self, *args, **kwargs):
        if self._db is not None:
            self._db.close()

    @property
    def db(self):
        if self._db is None:
            DATABASE_USER = os.getenv("DATABASE_USER")
            DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
            DATABASE_HOST = os.getenv("DATABASE_HOST", 'postgres')
            DATABASE_PORT = os.getenv("DATABASE_PORT", "5432")
            DATABASE_NAME = os.getenv("DATABASE_NAME",'enhanced_dataprep')

            DATABASE_URL = f"postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"

            engine = create_engine(DATABASE_URL)
            self._db = sessionmaker(autocommit=False, autoflush=False, bind=engine)()

        return self._db

    @property
    def minio(self):
        if self._minio is None:
            self._minio = get_local_minio_client()
        return self._minio

def response_err(response):
    try:
        return response.json().get('detail', response.text)
    except Exception:
        return response.text

@shared_task(base=WithEDPTask, bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 3})
def process_file_task(self, file_id: Any, *args, **kwargs):

    file_db = self.db.query(FileStatus).filter(FileStatus.id == file_id).first()
    if file_db is None:
        raise Exception(f"File with id {file_id} not found")

    logger.debug(f"[{file_db.id}] Started processing file.")

    file_db.status = 'processing'
    file_db.job_message = 'Data clean up in progress.'
    self.db.commit()

    # Step 0 - Delete everything related to the file in the vector database
    response = requests.post(f"{INGESTION_ENDPOINT}/delete", json={ 'file_id': str(file_db.id) })
    if response.status_code != 200:
        file_db.status = 'error'
        file_db.job_message = f"Error encountered while removing existing data related to file. {response_err(response)}"
        self.db.commit()
        raise Exception(f"Error encountered while data clean up. {response_err(response)}")
    logger.debug(f"[{file_db.id}] Deleted existing data related to file.")

    # Step 1 - Prepare the file for dataprep request
    file_db.dataprep_start = datetime.datetime.now()
    file_db.status = 'dataprep'
    file_db.job_message = 'Data preparation in progress.'
    self.db.commit()

    try:
        response = self.minio.get_object(bucket_name=file_db.bucket_name, object_name=file_db.object_name)
        file_data = response.read()
        file_base64 = base64.b64encode(file_data).decode('ascii')
        logger.debug(f"[{file_db.id}] Retrievied file from S3 storage.")
    except S3Error as e:
        file_db.status = 'error'
        file_db.job_message = f"Error downloading file. {e}"
        file_db.dataprep_end = datetime.datetime.now()
        self.db.commit()
        raise Exception(f"Error downloading file. {e}")
    finally:
        response.close()
        response.release_conn()

    # Step 2 - Call the data preparation service
    filename = file_db.object_name.split('/')[-1]
    response = requests.post(DATAPREP_ENDPOINT, json={ 'files': [{'filename': filename, 'data64': file_base64}] })
    if response.status_code != 200:
        file_db.status = 'error'
        file_db.job_message = f"Error encountered while data preparation. {response_err(response)}"
        file_db.dataprep_end = datetime.datetime.now()
        self.db.commit()
        raise Exception(f"Error encountered while data preparation. {response_err(response)}")
    logger.debug(f"[{file_db.id}] Data preparation completed.")

    dataprep_docs = []
    try:
        dataprep_docs = response.json()['docs']
        if len(dataprep_docs) == 0:
            logger.debug(f"[{file_db.id}] Data preparation returned 0 chunks.")
            raise Exception('No text extracted from the file.')

        file_db.chunk_size = len(dataprep_docs[0]) # Update chunk size
        file_db.chunks_total = len(dataprep_docs) # Update chunks count
        file_db.dataprep_end = datetime.datetime.now()
        self.db.commit()
    except Exception as e:
        file_db.status = 'error'
        file_db.job_message = 'No text extracted from the file.'
        file_db.dataprep_end = datetime.datetime.now()
        self.db.commit()
        raise Exception(f"Error parsing response from data preparation service. {e} {response.text}")

    # 2.1 Update the metadata info from database
    for doc in dataprep_docs:
        doc['metadata']['etag'] = file_db.etag
        doc['metadata']['bucket_name'] = file_db.bucket_name
        doc['metadata']['object_name'] = file_db.object_name
        doc['metadata']['file_id'] = str(file_db.id).replace('-', '') # uuid w/o hyphens because redis does not support search with hypens

    # Step 2.5 (Optional) - scan datapreped documents with Dataprep Guardrail
    dpguard_msg = ""
    dpguard_status = ""
    try:
        dpguard_enabled = os.getenv('DPGUARD_ENABLED', "false")
        logger.info(f"dpguard_enabled: {dpguard_enabled}")
        if dpguard_enabled == "true":
            file_db.dpguard_start = datetime.datetime.now()
            file_db.status = 'dpguard'
            file_db.job_message = 'Data Preparation Guardrail in progress.'
            self.db.commit()
            dpguard_endpoint   = os.environ.get('DPGUARD_ENDPOINT')
            logger.info(f"dpguard_endpoint: {dpguard_endpoint}")
            logger.info("Dataprep Guardrail enabled. Scanning the documents.")
            response = requests.post(dpguard_endpoint, json={ 'docs': dataprep_docs })
            if response.status_code != 200:
                dpguard_msg = 'Dataprep Guardrail failed.'
                dpguard_status = 'error'
                if response.status_code == 466:
                    dpguard_msg = "Dataprep Guardrail blocked embedding this document"
                    dpguard_status = 'blocked'
                raise Exception(f"{dpguard_msg} {response_err(response)}")
            file_db.dpguard_end = datetime.datetime.now()
            self.db.commit()
            logger.info("Dataprep Guardrail completed.")
    except Exception as e:
        file_db.job_message = dpguard_msg if dpguard_msg else 'Error while executing dataprep guardrail.'
        file_db.status = dpguard_status if dpguard_status else 'error'
        file_db.dpguard_end = datetime.datetime.now()
        self.db.commit()
        raise Exception(f"Error while executing dataprep guardrail. {e} {response.text}")

    # Step 3 - Call the embedding service and ingestion service in batches
    batch_size = os.getenv('BATCH_SIZE', 128)
    file_db.embedding_start = datetime.datetime.now()
    file_db.status = 'embedding'
    file_db.job_message = 'Data embedding in progress.'
    self.db.commit()
    for i in range(0, len(dataprep_docs), batch_size):
        # Step 3.1 - send each chunk of text from dataprep to the embedding service
        docs_batch = dataprep_docs[i:i+batch_size]
        response = requests.post(EMBEDDING_ENDPOINT, json={ "docs": docs_batch })
        logger.debug(f"[{file_db.id}] Chunk {i} embedding completed.")
        if response.status_code == 200:
            # Step 3.2 - save each chunk of text and embedding to the vector database
            response = requests.post(INGESTION_ENDPOINT, json=response.json()) # pass the whole response from embedding to ingestion
            logger.debug(f"[{file_db.id}] Chunk {i} ingestion completed.")
            if response.status_code != 200:
                file_db.status = 'error'
                file_db.job_message = f"Error encountered while ingestion. {response_err(response)}"
                file_db.embedding_end = datetime.datetime.now()
                self.db.commit()
                raise Exception(f"Error encountered while ingestion. {response_err(response)}")
        else:
            file_db.status = 'error'
            file_db.job_message = f"Error encountered while embedding. {response_err(response)}"
            file_db.embedding_end = datetime.datetime.now()
            self.db.commit()
            raise Exception(f"Error encountered while embedding. {response_err(response)}")

        # Update the pipeline progress
        file_db.chunks_processed = i + len(docs_batch)
        self.db.commit()

    # Update the processing time
    file_db.embedding_end = datetime.datetime.now()
    file_db.status = 'ingested'
    file_db.job_message = 'Data ingestion completed.'
    file_db.task_id = ""
    self.db.commit()
    logger.debug(f"[{file_db.id}] File stored successfully.")
    return True


@shared_task(base=WithEDPTask, bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 3})
def delete_file_task(self, file_id: Any, *args, **kwargs):
    file_db = self.db.query(FileStatus).filter(FileStatus.id == file_id).first()
    if file_db is None:
        raise Exception(f"File with id {file_id} not found")

    logger.debug(f"[{file_db.id}] Started processing file deletion.")

    # Step 1 - Delete everything related to the file in the vector database
    response = requests.post(f"{INGESTION_ENDPOINT}/delete", json={ 'file_id': str(file_db.id).replace('-', '') })
    logger.debug(f"[{file_db.id}] Deleted existing data related to file.")
    if response.status_code != 200:
        file_db.job_status = 'error'
        file_db.job_message = f"Error encountered while removing existing data related to file. {response_err(response)}"
        self.db.commit()
        raise Exception(f"Error encountered while data clean up. {response_err(response)}")

    # Step 2 - Delete the file from database
    id = file_db.id
    self.db.delete(file_db)
    logger.debug(f"[{id}] File deleted successfully from database.")
    return True


@shared_task(base=WithEDPTask, bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 3})
def process_link_task(self, link_id: Any, *args, **kwargs):
    link_db = self.db.query(LinkStatus).filter(LinkStatus.id == link_id).first()
    if link_db is None:
        raise Exception(f"Link with id {link_db} not found")

    logger.debug(f"[{link_db.id}] Started processing link.")

    link_db.status = 'processing'
    link_db.job_message = 'Data clean up in progress.'
    self.db.commit()

    # Step 0 - Delete everything related to the file in the vector database
    response = requests.post(f"{INGESTION_ENDPOINT}/delete", json={ 'link_id': str(link_db.id) })
    if response.status_code != 200:
        link_db.status = 'error'
        link_db.job_message = f"Error encountered while removing existing data related to file. {response_err(response)}"
        self.db.commit()
        raise Exception(f"Error encountered while data clean up. {response_err(response)}")
    logger.debug(f"[{link_db.id}] Deleted existing data related to link.")

    # Step 1 - Prepare the file for dataprep request
    link_db.dataprep_start = datetime.datetime.now()
    link_db.status = 'dataprep'
    link_db.job_message = 'Data preparation in progress.'
    self.db.commit()

    # Step 2 - Call the data preparation service
    response = requests.post(DATAPREP_ENDPOINT, json={ 'links': [link_db.uri] })
    if response.status_code != 200:
        link_db.status = 'error'
        link_db.job_message = f"Error encountered while data preparation. {response_err(response)}"
        link_db.dataprep_end = datetime.datetime.now()
        self.db.commit()
        raise Exception(f"Error encountered while data preparation. {response_err(response)}")
    logger.debug(f"[{link_db.id}] Data preparation completed.")

    dataprep_docs = []
    try:
        dataprep_docs = response.json()['docs']
        if len(dataprep_docs) == 0:
            logger.debug(f"[{link_db.id}] Data preparation returned 0 chunks.")
            raise Exception('No text extracted from the file.')

        link_db.chunk_size = len(dataprep_docs[0]) # Update chunk size
        link_db.chunks_total = len(dataprep_docs) # Update chunks count
        link_db.dataprep_end = datetime.datetime.now()
        self.db.commit()
    except Exception as e:
        link_db.status = 'error'
        link_db.job_message = 'No text extracted from the link.'
        link_db.dataprep_end = datetime.datetime.now()
        self.db.commit()
        raise Exception(f"Error parsing response from data preparation service. {e} {response.text}")

    # 2.1 Update the metadata info from database
    for doc in dataprep_docs:
        doc['metadata']['link_id'] = str(link_db.id).replace('-', '') # uuid w/o hyphens because redis does not support search with hypens

    # Step 2.5 (Optional) - scan datapreped documents with Dataprep Guardrail
    dpguard_msg = ""
    dpguard_status = ""
    try:
        dpguard_enabled = os.getenv('DPGUARD_ENABLED', "false")
        logger.info(f"dpguard_enabled: {dpguard_enabled}")
        if dpguard_enabled == "true":
            link_db.dpguard_start = datetime.datetime.now()
            link_db.status = 'dpguard'
            link_db.job_message = 'Data Preparation Guardrail in progress.'
            self.db.commit()
            dpguard_endpoint   = os.environ.get('DPGUARD_ENDPOINT')
            logger.info(f"dpguard_endpoint: {dpguard_endpoint}")
            logger.info("Dataprep Guardrail enabled. Scanning the documents.")
            response = requests.post(dpguard_endpoint, json={ 'docs': dataprep_docs })
            if response.status_code != 200:
                dpguard_msg = 'Dataprep Guardrail failed.'
                dpguard_status = 'error'
                if response.status_code == 466:
                    dpguard_msg = "Dataprep Guardrail blocked embedding this document"
                    dpguard_status = 'blocked'
                raise Exception(f"{dpguard_msg} {response_err(response)}")
            link_db.dpguard_end = datetime.datetime.now()
            self.db.commit()
            logger.info("Dataprep Guardrail completed.")
    except Exception as e:
        link_db.job_message = dpguard_msg if dpguard_msg else 'Error while executing dataprep guardrail.'
        link_db.status = dpguard_status if dpguard_status else 'error'
        link_db.dpguard_end = datetime.datetime.now()
        self.db.commit()
        raise Exception(f"Error while executing dataprep guardrail. {e} {response.text}")

    # Step 3 - Call the embedding service and ingestion service in batches
    batch_size = os.getenv('BATCH_SIZE', 128)
    link_db.embedding_start = datetime.datetime.now()
    link_db.status = 'embedding'
    link_db.job_message = 'Data embedding in progress.'
    self.db.commit()
    for i in range(0, len(dataprep_docs), batch_size):
        # Step 3.1 - send each chunk of text from dataprep to the embedding service
        docs_batch = dataprep_docs[i:i+batch_size]
        response = requests.post(EMBEDDING_ENDPOINT, json={ "docs": docs_batch })
        logger.debug(f"[{link_db.id}] Chunk {i} embedding completed.")
        if response.status_code == 200:
            # Step 3.2 - save each chunk of text and embedding to the vector database
            response = requests.post(INGESTION_ENDPOINT, json=response.json()) # pass the whole response from embedding to ingestion
            logger.debug(f"[{link_db.id}] Chunk {i} ingestion completed.")
            if response.status_code != 200:
                link_db.status = 'error'
                link_db.job_message = f"Error encountered while ingestion. {response_err(response)}"
                link_db.embedding_end = datetime.datetime.now()
                self.db.commit()
                raise Exception(f"Error encountered while ingestion. {response_err(response)}")
        else:
            link_db.status = 'error'
            link_db.job_message = f"Error encountered while embedding. {response_err(response)}"
            link_db.embedding_end = datetime.datetime.now()
            self.db.commit()
            raise Exception(f"Error encountered while embedding. {response_err(response)}")

        # Update the pipeline progress
        link_db.chunks_processed = i + len(docs_batch)
        self.db.commit()

    # Update the processing time
    link_db.embedding_end = datetime.datetime.now()
    link_db.status = 'ingested'
    link_db.job_message = 'Data ingestion completed.'
    link_db.task_id = ""
    self.db.commit()
    logger.debug(f"[{link_db.id}] File stored successfully.")
    return True


@shared_task(base=WithEDPTask, bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 3})
def delete_link_task(self, link_id: Any, *args, **kwargs):
    link_db = self.db.query(LinkStatus).filter(LinkStatus.id == link_id).first()
    if link_db is None:
        raise Exception(f"Link with id {link_id} not found")

    logger.debug(f"[{link_db.id}] Started processing file deletion.")

    # Step 1 - Delete everything related to the file in the vector database
    response = requests.post(f"{INGESTION_ENDPOINT}/delete", json={ 'link_id': str(link_db.id).replace('-', '') })
    logger.debug(f"[{link_db.id}] Deleted existing data related to file.")
    if response.status_code != 200:
        link_db.job_status = 'error'
        link_db.job_message = f"Error encountered while removing existing data related to file. {response_err(response)}"
        self.db.commit()
        raise Exception(f"Error encountered while data clean up. {response_err(response)}")

    # Step 2 - Delete the file from database
    id = link_db.id
    self.db.delete(link_db)
    logger.debug(f"[{id}] File deleted successfully from database.")
    return True
