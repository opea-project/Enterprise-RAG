// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ServiceArgumentInputMessage.scss";

import classNames from "classnames";

interface ServiceArgumentInputMessageProps {
  message: string;
  forFocus?: boolean;
  forInvalid?: boolean;
}

const ServiceArgumentInputMessage = ({
  message,
  forFocus,
  forInvalid,
}: ServiceArgumentInputMessageProps) => {
  const messageClassNames = classNames({
    "service-argument-input-message": true,
    "service-argument-input-message__on-focus": forFocus,
    "service-argument-input-message__on-invalid": forInvalid,
  });

  return (
    <div className={messageClassNames}>
      <p>{message}</p>
    </div>
  );
};

export default ServiceArgumentInputMessage;
