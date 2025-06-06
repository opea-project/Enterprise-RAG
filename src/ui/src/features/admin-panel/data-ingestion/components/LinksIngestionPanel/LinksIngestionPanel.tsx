// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Dispatch, SetStateAction } from "react";
import { v4 as uuidv4 } from "uuid";

import LinkInput from "@/features/admin-panel/data-ingestion/components/LinkInput/LinkInput";
import LinksList from "@/features/admin-panel/data-ingestion/components/LinksList/LinksList";
import { LinkForIngestion } from "@/features/admin-panel/data-ingestion/types";

interface LinksIngestionPanelProps {
  links: LinkForIngestion[];
  setLinks: Dispatch<SetStateAction<LinkForIngestion[]>>;
}

const LinksIngestionPanel = ({ links, setLinks }: LinksIngestionPanelProps) => {
  const addLinkToList = (value: string) => {
    setLinks((prevState) => [
      ...prevState,
      {
        id: uuidv4(),
        value,
      },
    ]);
  };

  const removeLinkFromList = (linkId: string) => {
    setLinks((prevState) => prevState.filter((link) => link.id !== linkId));
  };

  return (
    <section>
      <h2>Links</h2>
      <p className="mb-2 text-xs">
        Supported text-based links extensions: ADOC, PDF, HTML, TXT, DOC, DOCX,
        PPT, PPTX, MD, XML, JSON, JSONL, YAML, XLS, XLSX, CSV, TIFF, JPG, JPEG,
        PNG, SVG
      </p>
      <LinkInput addLinkToList={addLinkToList} />
      {links.length > 0 && (
        <LinksList
          links={links}
          setLinks={setLinks}
          removeLinkFromList={removeLinkFromList}
        />
      )}
    </section>
  );
};

export default LinksIngestionPanel;
