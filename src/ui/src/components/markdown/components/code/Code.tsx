// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import classNames from "classnames";
import { HTMLAttributes, PropsWithChildren } from "react";

import CopyButton from "@/components/ui/CopyButton/CopyButton";
import parseChildrenTextContent from "@/components/utils/parseChildrenTextContent";

import styles from "./Code.module.scss";

export const Pre = ({ children }: PropsWithChildren) => {
  const rawCode =
    children !== null && typeof children === "object" && "props" in children
      ? children.props.children
      : "";

  return (
    <div className={styles.preWrapper}>
      <pre className={styles.pre}>{children}</pre>
      <CopyButton textToCopy={rawCode} />
    </div>
  );
};

type CodeProps = PropsWithChildren<
  Pick<HTMLAttributes<HTMLElement>, "className">
> & {
  inline?: boolean;
};

export const Code = ({ children, className }: CodeProps) => (
  <code className={classNames(styles.code, className)}>
    {parseChildrenTextContent(children)}
  </code>
);
