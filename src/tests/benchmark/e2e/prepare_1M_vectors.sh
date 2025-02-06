#!/bin/bash
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

redis_get_vectors()
{
	NS=chatqa
	APP=redis-vector-db
	SECRET=vector-database-config

	REDIS_PASS=$(kubectl get secret --namespace $NS $SECRET -o jsonpath="{.data.REDIS_PASSWORD}" | base64 --decode)
	CONTAINER_NAME=$(kubectl get pods --namespace $NS -l app=$APP -o jsonpath='{.items[*].metadata.name}')
	vectors=$(kubectl exec -it $CONTAINER_NAME --namespace $NS -- redis-cli -a "$REDIS_PASS" ft.info default_index | grep num_docs -A 1 | tail -n1 | rev | cut -d " " -f1 | rev)
	echo "current vectors in Redis: $vectors"
	vectors="${vectors//[$'\t\r\n ']}"
	export REDIS_VECTORS=$vectors
}

wait_for_ingest()
{
	sleep 60
	while true
	do
		redis_get_vectors
		completed="yes"
		upload_stat=$(curl -k -s ${EDP_URL}/files -H "Authorization: Bearer ${USER_ACCESS_TOKEN}")
		while read -r status; do
			echo "status: $status"
			if [[ "$status" != "error" ]] && [[ "$status" != "ingested" ]]; then
				completed="no"
			fi
		done < <(echo $upload_stat | jq -r '.[].status')
		echo "completed $completed"
		if [[ "$completed" == "yes" ]]; then
			echo "breaking"
			break
		fi
		echo "waiting for file upload"
		sleep 120
	done
}

upload_file()
{
	filename=$1
	tmpstr="{ \"bucket_name\": \"default\", \"object_name\": \"${filename}\", \"method\": \"PUT\" }"
	echo $tmpstr > /tmp/dataprep.json
	curloutput=$(curl -k --no-buffer "${EDP_URL}/presignedUrl" -X POST -d @/tmp/dataprep.json -H 'Content-Type: application/json' -H "Authorization: Bearer ${USER_ACCESS_TOKEN}")
	furl=$(echo $curloutput | jq -r '.url')
	curl -k -X PUT -T "$TEMP_DIR/$filename" "$furl"
}

upload_relevant_documents()
{
	orig_dir=$(pwd)
	mkdir -p $TEMP_DIR

	cd $TEMP_DIR
	echo "downloading documents"
	while IFS= read -r line
	do
		echo $line
		wget --adjust-extension  $line
	done < "${orig_dir}/documents.txt"

	for filename in *.utf-8; do
		filename=$(basename ${filename})
		fn2="${filename/.utf-8/}"
		mv $filename $fn2
	done

	cd $orig_dir
	echo "ingesting documents into rag"
	source generate_uat.sh
	for filename in $TEMP_DIR/*; do
		filename=$(basename ${filename})
		upload_file $filename
		sleep 1
	done
	sleep 5
	rm -rf $TEMP_DIR

	wait_for_ingest
}

fill_with_wikipedia()
{
	orig_dir=$(pwd)
	echo "parsing wiki"
	mkdir -p $TEMP_DIR
	cd $TEMP_DIR
	wget https://dumps.wikimedia.org/simplewiki/latest/simplewiki-latest-pages-articles-multistream.xml.bz2
	bzip2 -d "simplewiki-latest-pages-articles-multistream.xml.bz2"

	cd $orig_dir
	python3 wikiparse.py "${TEMP_DIR}/simplewiki-latest-pages-articles-multistream.xml" $TEMP_DIR
	rm -rf "${TEMP_DIR}/simplewiki-latest-pages-articles-multistream.xml"

	echo "ingesting wiki into rag"
	for filename in $TEMP_DIR/*; do
		filename=$(basename ${filename})
		source generate_uat.sh
		upload_file $filename
		wait_for_ingest
		redis_get_vectors
		if [ "$REDIS_VECTORS" -gt "$EXPECTED_VECTORS" ]; then
			break
		fi
	done
	rm -rf $TEMP_DIR
}

export TEMP_DIR="/tmp/ragdocumentsedp"
export EDP_URL="https://erag.com/api/v1/edp"
export EXPECTED_VECTORS=1000000

rm -rf $TEMP_DIR
upload_relevant_documents
fill_with_wikipedia
rm -rf /tmp/dataprep.json
