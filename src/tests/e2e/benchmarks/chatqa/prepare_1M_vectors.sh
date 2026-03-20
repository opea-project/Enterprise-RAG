#!/bin/bash
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

refresh_uat()
{
	source generate_uat_to_file.sh "/dev/null" 1
	if [[ -z "$USER_ACCESS_TOKEN" ]] || [[ "$USER_ACCESS_TOKEN" == "null" ]]; then
		echo "Error: failed to generate user access token"
		exit 1
	fi
}

count_vectors()
{
	total_files=0
	total_chunks=0
	in_progress=0
	te_duration=0
	tc_duration=0
	ts_duration=0
	guard_duration=0
	embed_duration=0
	process_duration=0
	upload_stat=$(curl -k -s ${EDP_URL}/files -H "Authorization: Bearer ${USER_ACCESS_TOKEN}")
	while read -r details; do
		status=$(echo "$details" | jq -r .status)
		if [[ "$status" == "ingested" ]]; then
			chunks=$(echo "$details" | jq -r .chunks_processed)
			d1=$(echo "$details" | jq -r .text_extractor_duration)
			d2=$(echo "$details" | jq -r .text_compression_duration)
			d3=$(echo "$details" | jq -r .text_splitter_duration)
			d4=$(echo "$details" | jq -r .dpguard_duration)
			d5=$(echo "$details" | jq -r .embedding_duration)
			d6=$(echo "$details" | jq -r .processing_duration)
			total_files=$(($total_files + 1))
			total_chunks=$(($total_chunks + $chunks))
			te_duration=$(($te_duration + $d1))
			tc_duration=$(($tc_duration + $d2))
			ts_duration=$(($ts_duration + $d3))
			guard_duration=$(($guard_duration + $d4))
			embed_duration=$(($embed_duration + $d5))
			process_duration=$(($process_duration + $d6))
		fi
		if [[ "$status" != "error" ]] && [[ "$status" != "ingested" ]]; then
			in_progress=$(($in_progress + 1))
		fi
	done < <(echo $upload_stat | jq -c '.[]')
	echo "total files during processing (in progress): $in_progress"
	echo "total ingested files: $total_files vectors (chunks): $total_chunks text extractor duration: $te_duration text compression duration: $tc_duration text splitter duration $ts_duration dpguard duration: $guard_duration embedding duration: $embed_duration processing duration: $process_duration"
	export DB_VECTORS=$total_chunks
	export IN_PROGRESS=$in_progress
}

wait_for_ingest()
{
	sleep 60
	refresh_uat
	while true
	do
		count_vectors
		if [[ "$IN_PROGRESS" -eq 0 ]]; then
			break
		fi
		echo "waiting 30 seconds to verify if ingestion process is completed"
		sleep 30
	done
}

upload_file()
{
	filename=$1
	echo "uploading $filename"
	tmpstr="{ \"bucket_name\": \"default\", \"object_name\": \"${filename}\", \"method\": \"PUT\" }"
	echo $tmpstr > /tmp/dataprep.json
	curloutput=$(curl -k --no-buffer "${EDP_URL}/presignedUrl" -X POST -d @/tmp/dataprep.json -H 'Content-Type: application/json' -H "Authorization: Bearer ${USER_ACCESS_TOKEN}")
	furl=$(echo $curloutput | jq -r '.url')
	curl -k -X PUT -H "Authorization: Bearer ${USER_ACCESS_TOKEN}" -T "$TEMP_DIR/$filename" "$furl"
}

upload_relevant_documents()
{
	orig_dir=$(pwd)
	mkdir -p $TEMP_DIR
	exp_documents=$(cat documents.csv | wc -l)

	cd $TEMP_DIR
	echo "downloading documents"
	while IFS=';' read -r url output; do
		echo "Downloading $url and saving as $output"
		wget -q $url -O $output
	done < "${orig_dir}/documents.csv"

	cd $orig_dir
	avail_documents=$(ls $TEMP_DIR | wc -l)
	echo "downloaded $avail_documents of $exp_documents expected documents"

	echo "ingesting documents into rag"
	for filename in $TEMP_DIR/*; do
		filename=$(basename ${filename})
		upload_file $filename
		sleep 1
	done
	sleep 5
	rm -rf $TEMP_DIR
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
	# EDP process two files in parallel, so uploading two files in parallel improves the performance
	file_list=("$TEMP_DIR"/*)
	file_list_cnt=${#file_list[@]}
	for ((fid=0; fid<$file_list_cnt; fid+=2)); do
		wait_for_ingest
		if [ "$DB_VECTORS" -gt "$EXPECTED_VECTORS" ]; then
			echo "Number of expected vectors are met, exiting"
			rm -rf $TEMP_DIR
			return 0
		fi
		file1=$(basename ${file_list[$fid]})
		upload_file $file1
		if [[ "${file_list[$fid+1]}" ]]; then
			file2=$(basename ${file_list[$fid+1]})
			upload_file $file2
		fi
	done
	wait_for_ingest
	rm -rf $TEMP_DIR
}

export TEMP_DIR="/tmp/ragdocumentsedp"
export EDP_URL="https://${ERAG_DOMAIN_NAME:-erag.com}/api/v1/edp"
export EXPECTED_VECTORS=${1:-1000000}
if [ -n "$1" ]; then
	echo "Using non-default value for EXPECTED_VECTORS: $EXPECTED_VECTORS"
else
	echo "Using default value for EXPECTED_VECTORS: $EXPECTED_VECTORS"
fi

refresh_uat
count_vectors
if [ "$DB_VECTORS" -gt "$EXPECTED_VECTORS" ]; then
	echo "Number of expected vectors are met, exiting"
	exit 0
fi

rm -rf $TEMP_DIR
upload_relevant_documents
fill_with_wikipedia
rm -rf /tmp/dataprep.json
