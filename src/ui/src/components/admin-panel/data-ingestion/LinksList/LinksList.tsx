// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./LinksList.scss";

import { Dispatch, SetStateAction } from "react";
import { BsTrash } from "react-icons/bs";

import ListHeader from "@/components/admin-panel/data-ingestion/ListHeader/ListHeader";
import { LinkForIngestion } from "@/models/admin-panel/data-ingestion/dataIngestion";

interface LinksListProps {
  links: LinkForIngestion[];
  setLinks: Dispatch<SetStateAction<LinkForIngestion[]>>;
  removeLinkFromList: (id: string) => void;
  disabled: boolean;
}

const LinksList = ({
  links,
  setLinks,
  disabled,
  removeLinkFromList,
}: LinksListProps) => {
  const clearList = () => {
    setLinks([]);
  };

  return (
    <>
      <ListHeader disabled={disabled} onClearListBtnClick={clearList} />
      <ul>
        {links.map(({ id, value }) => (
          <li key={id} className="link-list-item">
            <p className="link-list-item__url">{value}</p>
            <button
              className="icon-button-outlined--danger"
              disabled={disabled}
              onClick={() => removeLinkFromList(id)}
            >
              <BsTrash size={16} />
            </button>
          </li>
        ))}
      </ul>
    </>
  );
};

export default LinksList;
