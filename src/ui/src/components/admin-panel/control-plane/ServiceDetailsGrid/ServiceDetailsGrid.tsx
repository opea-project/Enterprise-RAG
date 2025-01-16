// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ServiceDetailsGrid.scss";

import { Fragment } from "react";

import { ServiceDetails } from "@/models/admin-panel/control-plane/serviceData";

const formatLabel = (label: string) => {
  let labelWords = label.split("_");
  labelWords = labelWords.map((word) => {
    if (["LLM", "DB"].includes(word)) {
      return word;
    }

    word = word.toLowerCase();
    return `${word.slice(0, 1).toUpperCase()}${word.slice(1)}`;
  });
  return labelWords.join(" ");
};

interface ServiceDetailsGridProps {
  details: ServiceDetails;
}

const ServiceDetailsGrid = ({ details }: ServiceDetailsGridProps) => (
  <section className="service-details-grid">
    {Object.entries(details).map(([label, value]) => (
      <Fragment key={label}>
        <p className="service-detail-label">{formatLabel(label)}</p>
        <p className="service-detail-value">{value}</p>
      </Fragment>
    ))}
  </section>
);

export default ServiceDetailsGrid;
