// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { OlHTMLAttributes, PropsWithChildren } from "react";

import styles from "./Lists.module.scss";

export const UnorderedList = ({ children }: PropsWithChildren) => (
  <ul className={styles.ul}>{children}</ul>
);

type OrderedListProps = PropsWithChildren<
  Pick<OlHTMLAttributes<HTMLOListElement>, "start">
>;

export const OrderedList = ({ children, start }: OrderedListProps) => (
  <ol className={styles.ol} start={start}>
    {children}
  </ol>
);

export const ListItem = ({ children }: PropsWithChildren) => (
  <li className={styles.li}>{children}</li>
);
