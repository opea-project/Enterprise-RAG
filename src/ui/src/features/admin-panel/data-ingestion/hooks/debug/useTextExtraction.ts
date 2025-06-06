// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  usePostFileToExtractTextMutation,
  usePostLinkToExtractTextMutation,
} from "@/features/admin-panel/data-ingestion/api/edpApi";
import { PostToExtractTextQueryParams } from "@/features/admin-panel/data-ingestion/types/api";
import { getErrorMessage } from "@/utils/api";

type PostToExtractTextMutationHook =
  | typeof usePostFileToExtractTextMutation
  | typeof usePostLinkToExtractTextMutation;

const useTextExtraction = (
  usePostToExtractTextMutation: PostToExtractTextMutationHook,
  fallbackErrorMessage: string,
  uuid: string,
) => {
  const [postExtract, { data, isLoading, error }] =
    usePostToExtractTextMutation();

  const onTriggerPress = () => {
    postExtract({ uuid });
  };

  const onFormSubmit = (
    queryParams: PostToExtractTextQueryParams,
    isFormEnabled: boolean,
  ) => {
    if (isFormEnabled) {
      postExtract({ uuid, queryParams });
    } else {
      postExtract({ uuid });
    }
  };

  const errorMessage = error
    ? getErrorMessage(error, fallbackErrorMessage)
    : undefined;

  return {
    extractedText: data,
    isLoading,
    errorMessage,
    onTriggerPress,
    onFormSubmit,
  };
};

export default useTextExtraction;
