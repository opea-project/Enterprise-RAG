// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./LinksList.scss";

import { Dispatch, SetStateAction } from "react";

import ListHeader from "@/components/admin-panel/data-ingestion/ListHeader/ListHeader";
import IconButton from "@/components/shared/IconButton/IconButton";
import { LinkForIngestion } from "@/models/admin-panel/data-ingestion/dataIngestion";

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
      <ListHeader onClearListBtnClick={clearList} />
      <ul>
        {links.map(({ id, value }) => (
          <li key={id} className="link-list-item">
            <p className="link-list-item__url">{value}</p>
            <IconButton
              icon="delete"
              color="error"
              onClick={() => removeLinkFromList(id)}
            />
          </li>
        ))}
      </ul>
    </>
  );
};

export default LinksList;
