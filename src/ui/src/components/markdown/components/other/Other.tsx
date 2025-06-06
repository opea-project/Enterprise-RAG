// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ImgHTMLAttributes, PropsWithChildren } from "react";

import Anchor, { AnchorProps } from "@/components/ui/Anchor/Anchor";

import styles from "./Other.module.scss";

type AProps = PropsWithChildren<Pick<AnchorProps, "href">>;

export const A = ({ children, href }: AProps) => (
  <Anchor href={href}>{children}</Anchor>
);

type ImgProps = Pick<
  ImgHTMLAttributes<HTMLImageElement>,
  "src" | "alt" | "title"
>;

export const Img = ({ src, alt, title }: ImgProps) => (
  <img className={styles.img} src={src} alt={alt} title={title} />
);

export const Hr = () => <hr className={styles.hr} />;
