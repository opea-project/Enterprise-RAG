// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Children, cloneElement, isValidElement, ReactNode } from "react";
import { v4 as uuidv4 } from "uuid";

import HomoglyphTextMarker from "@/components/shared/HomoglyphTextMarker/HomoglyphTextMarker";
import { isPunycodeSafe } from "@/utils/validators";

const isPotentialHomoglyph = (originalText: string) =>
  !isPunycodeSafe(originalText);

const highlightPotentialHomoglyphs = (textContent: string) => {
  const elements: ReactNode[] = [];
  let homoglyphBuffer = "";
  let textBuffer = "";

  const flushTextBuffer = () => {
    if (textBuffer) {
      elements.push(textBuffer);
      textBuffer = "";
    }
  };

  const flushHomoglyphBuffer = () => {
    if (homoglyphBuffer) {
      elements.push(
        <HomoglyphTextMarker key={uuidv4()} text={homoglyphBuffer} />,
      );
      homoglyphBuffer = "";
    }
  };

  for (const char of textContent) {
    if (isPotentialHomoglyph(char)) {
      flushTextBuffer();
      homoglyphBuffer = homoglyphBuffer.concat(char);
    } else {
      flushHomoglyphBuffer();
      textBuffer = textBuffer.concat(char);
    }
  }

  flushTextBuffer();
  flushHomoglyphBuffer();

  return Children.toArray(elements);
};

const parseChildrenTextContent = (children: ReactNode): ReactNode =>
  Children.map(children, (child) => {
    const isChildTextContent =
      typeof child === "string" || typeof child === "number";

    if (isChildTextContent) {
      return highlightPotentialHomoglyphs(child.toString());
    } else if (isValidElement(child) && child.props.children) {
      const newChildren = parseChildrenTextContent(child.props.children);
      return cloneElement(child, {
        ...child.props,
        children: newChildren,
      });
    }
  });

export default parseChildrenTextContent;
