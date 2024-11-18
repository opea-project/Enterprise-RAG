// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ExternalLink.scss";

import { BsBoxArrowUpRight } from "react-icons/bs";

interface ExternalLinkProps {
  text: string;
  href: string;
}

const ExternalLink = ({ text, href }: ExternalLinkProps) => (
  <a className="external-link" href={href} target="_blank">
    {text}
    <BsBoxArrowUpRight size={12} />
  </a>
);

export default ExternalLink;
