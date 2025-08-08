// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useRef, useState } from "react";

const usePopover = <T>() => {
  const [isOpen, setIsOpen] = useState(false);
  const triggerRef = useRef<T | null>(null);

  const togglePopover = () => {
    setIsOpen((prev) => !prev);
  };

  return {
    isOpen,
    togglePopover,
    triggerRef,
  };
};

export default usePopover;
