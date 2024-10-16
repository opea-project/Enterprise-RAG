// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Dispatch, SetStateAction } from "react";
import { v4 as uuidv4 } from "uuid";

import LinkInput from "@/components/admin-panel/data-ingestion/LinkInput/LinkInput";
import LinksList from "@/components/admin-panel/data-ingestion/LinksList/LinksList";
import { LinkForIngestion } from "@/models/admin-panel/data-ingestion/dataIngestion";

interface LinksIngestionPanelProps {
  links: LinkForIngestion[];
  setLinks: Dispatch<SetStateAction<LinkForIngestion[]>>;
  disabled: boolean;
}

const LinksIngestionPanel = ({
  links,
  setLinks,
  disabled,
}: LinksIngestionPanelProps) => {
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
      <LinkInput addLinkToList={addLinkToList} disabled={disabled} />
      {links.length > 0 && (
        <LinksList
          links={links}
          setLinks={setLinks}
          disabled={disabled}
          removeLinkFromList={removeLinkFromList}
        />
      )}
    </section>
  );
};

export default LinksIngestionPanel;
