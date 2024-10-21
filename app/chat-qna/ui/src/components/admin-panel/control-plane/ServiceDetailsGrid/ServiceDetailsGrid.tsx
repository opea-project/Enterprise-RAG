// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ServiceDetailsGrid.scss";

import { Fragment } from "react";

import { ServiceDetails } from "@/models/admin-panel/control-plane/serviceData";

interface ServiceDetailsGridProps {
  details: ServiceDetails;
}

const ServiceDetailsGrid = ({ details }: ServiceDetailsGridProps) => (
  <section className="service-details-grid">
    {Object.entries(details).map(([label, value]) => (
      <Fragment key={label}>
        <p className="service-detail-label">{label}</p>
        <p className="service-detail-value">{value}</p>
      </Fragment>
    ))}
  </section>
);

export default ServiceDetailsGrid;
