// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ExternalLink.scss";

import CropSquareIcon from "@mui/icons-material/CropSquare";
import NorthEastIcon from "@mui/icons-material/NorthEast";
import { Link } from "@mui/material";

interface ExternalLinkProps {
  text: string;
  href: string;
}

const ExternalLink = ({ text, href }: ExternalLinkProps) => (
  <Link href={href} target="_blank">
    {text}
    <span className="external-link-icon-wrapper">
      <CropSquareIcon className="external-link-icon square-icon" />
      <NorthEastIcon className="external-link-icon arrow-icon" />
    </span>
  </Link>
);

export default ExternalLink;
