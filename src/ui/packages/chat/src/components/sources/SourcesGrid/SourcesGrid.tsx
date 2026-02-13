// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./SourcesGrid.scss";

import { Button } from "@intel-enterprise-rag-ui/components";
import { useState } from "react";

import { FileSourceDialog } from "@/components/sources/FileSourceDialog/FileSourceDialog";
import { LinkSourceDialog } from "@/components/sources/LinkSourceDialog/LinkSourceDialog";
import { SourceDocumentType } from "@/types";

const VISIBLE_SOURCES_OFFSET = 3;

interface SourcesGridProps {
  sources: SourceDocumentType[];
  onFileDownload: (fileName: string, bucketName: string) => void;
}

export const SourcesGrid = ({ sources, onFileDownload }: SourcesGridProps) => {
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
      <div className="sources-grid">
        {visibleSources.map((source, index) => {
          if (source.type === "file") {
            return (
              <FileSourceDialog
                key={index}
                source={source}
                onDownload={onFileDownload}
              />
            );
          } else if (source.type === "link") {
            return <LinkSourceDialog key={index} source={source} />;
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
