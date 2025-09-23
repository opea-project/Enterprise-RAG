// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { PropsWithChildren } from "react";

import styles from "./Typography.module.scss";

export const H1 = ({ children }: PropsWithChildren) => (
  <h1 className={styles.h1}>{children}</h1>
);

export const H2 = ({ children }: PropsWithChildren) => (
  <h2 className={styles.h2}>{children}</h2>
);

export const H3 = ({ children }: PropsWithChildren) => (
  <h3 className={styles.h3}>{children}</h3>
);

export const H4 = ({ children }: PropsWithChildren) => (
  <h4 className={styles.h4}>{children}</h4>
);

export const H5 = ({ children }: PropsWithChildren) => (
  <h5 className={styles.h5}>{children}</h5>
);

export const H6 = ({ children }: PropsWithChildren) => (
  <h6 className={styles.h6}>{children}</h6>
);

export const P = ({ children }: PropsWithChildren) => (
  <p className={styles.p}>{children}</p>
);

export const Strong = ({ children }: PropsWithChildren) => (
  <strong className={styles.strong}>{children}</strong>
);

export const Em = ({ children }: PropsWithChildren) => (
  <em className={styles.em}>{children}</em>
);

export const Del = ({ children }: PropsWithChildren) => (
  <del className={styles.del}>{children}</del>
);

export const Blockquote = ({ children }: PropsWithChildren) => (
  <blockquote className={styles.blockquote}>{children}</blockquote>
);
