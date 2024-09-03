// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./LinksList.scss";

import DeleteIcon from "@mui/icons-material/Delete";
import { List, ListItem, Typography } from "@mui/material";
import { Dispatch, SetStateAction } from "react";

import ListHeader from "@/components/admin-panel/data-ingestion/ListHeader/ListHeader";
import SquareIconButton from "@/components/shared/SquareIconButton/SquareIconButton";
import { LinkForIngestion } from "@/models/dataIngestion";

interface LinksListProps {
  links: LinkForIngestion[];
  setLinks: Dispatch<SetStateAction<LinkForIngestion[]>>;
  removeLinkFromList: (id: string) => void;
  disabled: boolean;
}

const LinksList = ({
  links,
  setLinks,
  removeLinkFromList,
  disabled,
}: LinksListProps) => {
  const clearList = () => {
    setLinks([]);
  };

  const clearListBtnDisabled = links.length === 0 || disabled;

  return (
    <>
      <ListHeader
        clearListBtnDisabled={clearListBtnDisabled}
        onClearListBtnClick={clearList}
      />
      <List>
        {links.map(({ id, value }) => (
          <ListItem key={id} className="link-list-item">
            <Typography variant="body2">{value}</Typography>
            <SquareIconButton
              color="error"
              disabled={disabled}
              onClick={() => removeLinkFromList(id)}
            >
              <DeleteIcon fontSize="small" />
            </SquareIconButton>
          </ListItem>
        ))}
      </List>
    </>
  );
};

export default LinksList;
