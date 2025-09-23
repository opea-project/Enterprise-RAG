// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { nullCharsRegex } from "@/utils/validators/constants";

const containsNullCharacters = (input: string) => nullCharsRegex.test(input);

export { containsNullCharacters };
