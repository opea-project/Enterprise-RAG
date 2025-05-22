// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./LinksList.scss";

import { Dispatch, SetStateAction } from "react";

import IconButton from "@/components/ui/IconButton/IconButton";
import ListHeader from "@/features/admin-panel/data-ingestion/components/ListHeader/ListHeader";
import { LinkForIngestion } from "@/features/admin-panel/data-ingestion/types";

interface LinksListProps {
  links: LinkForIngestion[];
  setLinks: Dispatch<SetStateAction<LinkForIngestion[]>>;
  removeLinkFromList: (id: string) => void;
}

const LinksList = ({ links, setLinks, removeLinkFromList }: LinksListProps) => {
  const clearList = () => {
    setLinks([]);
  };

  return (
    <>
      <ListHeader onClearListBtnPress={clearList} />
      <ul>
        {links.map(({ id, value }) => (
          <li key={id} className="link-list-item">
            <p className="link-list-item__url">{value}</p>
            <IconButton
              icon="delete"
              color="error"
              aria-label="Delete link from the list"
              onPress={() => removeLinkFromList(id)}
            />
          </li>
        ))}
      </ul>
    </>
  );
};

export default LinksList;
