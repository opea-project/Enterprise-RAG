// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./LinksList.scss";

import { IconButton } from "@intel-enterprise-rag-ui/components";
import classNames from "classnames";
import { Dispatch, SetStateAction } from "react";

import ListHeader from "@/features/admin-panel/data-ingestion/components/ListHeader/ListHeader";
import { LinkForIngestion } from "@/features/admin-panel/data-ingestion/types";

interface LinksListProps {
  links: LinkForIngestion[];
  setLinks: Dispatch<SetStateAction<LinkForIngestion[]>>;
  removeLinkFromList: (id: string) => void;
  highlightedLinkId?: string | null;
}

const LinksList = ({
  links,
  setLinks,
  removeLinkFromList,
  highlightedLinkId,
}: LinksListProps) => {
  const clearList = () => {
    setLinks([]);
  };

  return (
    <>
      <ListHeader onClearListBtnPress={clearList} />
      <ul>
        {links.map(({ id, value }) => (
          <li key={id} className="link-list-item">
            <p
              className={classNames("link-list-item__url", {
                highlighted: id === highlightedLinkId,
              })}
            >
              {value}
            </p>
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
