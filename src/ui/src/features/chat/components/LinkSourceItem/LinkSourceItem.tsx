// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import LinkIcon from "@/components/icons/LinkIcon/LinkIcon";
import Anchor from "@/components/ui/Anchor/Anchor";
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
