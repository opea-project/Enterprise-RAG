// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Button } from "@intel-enterprise-rag-ui/components";
import { useState } from "react";

import FileSourceItem from "@/features/chat/components/FileSourceItem/FileSourceItem";
import LinkSourceItem from "@/features/chat/components/LinkSourceItem/LinkSourceItem";
import { SourceDocumentType } from "@/features/chat/types";

const VISIBLE_SOURCES_OFFSET = 3;

interface SourcesGridProps {
  sources: SourceDocumentType[];
}

const SourcesGrid = ({ sources }: SourcesGridProps) => {
  const [allSourcesVisible, setAllSourcesVisible] = useState(false);

  const visibleSources = allSourcesVisible
    ? sources
    : sources.slice(0, VISIBLE_SOURCES_OFFSET);

  const handleBtnPress = () => {
    setAllSourcesVisible((prev) => !prev);
  };

  const isShowMoreBtnVisible = sources.length > VISIBLE_SOURCES_OFFSET;

  return (
    <>
      <div className="mt-2 grid grid-cols-3 gap-2">
        {visibleSources.map((source, index) => {
          if (source.type === "file") {
            return <FileSourceItem key={index} source={source} />;
          } else if (source.type === "link") {
            return <LinkSourceItem key={index} source={source} />;
          }
          return null;
        })}
      </div>
      {isShowMoreBtnVisible && (
        <Button
          variant="outlined"
          size="sm"
          className="float-right mt-2"
          onPress={handleBtnPress}
        >
          Show {allSourcesVisible ? "less" : "all"} sources
        </Button>
      )}
    </>
  );
};

export default SourcesGrid;
