// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Anchor } from "@intel-enterprise-rag-ui/components";
import { LinkIcon } from "@intel-enterprise-rag-ui/icons";

import SourceItem from "@/features/chat/components/SourceItem/SourceItem";
import { LinkSource } from "@/features/chat/types";

interface LinkSourceItemProps {
  source: LinkSource;
}

const LinkSourceItem = ({ source: { url } }: LinkSourceItemProps) => (
  <Anchor href={url}>
    <SourceItem icon={<LinkIcon />} name={url} />
  </Anchor>
);

export default LinkSourceItem;
