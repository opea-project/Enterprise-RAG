#!/bin/bash
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

fname=$1
sessions=$2
rm -rf $fname
for i in $(seq 1 ${sessions}); do
	source generate_uat.sh
	echo $USER_ACCESS_TOKEN | tee -a $fname
done
