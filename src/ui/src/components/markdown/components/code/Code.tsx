// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import classNames from "classnames";
import { HTMLAttributes, PropsWithChildren, useMemo } from "react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import {
  oneDark,
  oneLight,
} from "react-syntax-highlighter/dist/esm/styles/prism";

import CopyButton from "@/components/ui/CopyButton/CopyButton";
import { getPreDetails } from "@/components/utils/markdown";
import parseChildrenTextContent from "@/components/utils/parseChildrenTextContent";
import useColorScheme from "@/hooks/useColorScheme";

import styles from "./Code.module.scss";

export const Pre = ({ children }: PropsWithChildren) => {
  const { languageDisplayName, rawCode } = getPreDetails(children);
  const content = useMemo(() => {
    // check if children is a valid React element with props
    // without this "undefined" string will be displayed inside code block when children.props.children is missing
    const isValid =
      typeof children === "object" &&
      children !== null &&
      "props" in children &&
      children.props.children !== undefined;

    return isValid ? children : null;
  }, [children]);

  return (
    <div className={styles.preWrapper} role="region">
      <div className={styles.preWrapper__header}>
        <span className={styles.preWrapper__language}>
          {languageDisplayName}
        </span>
        <CopyButton textToCopy={rawCode} forCodeSnippet />
      </div>
      <pre className={styles.pre}>{content}</pre>
    </div>
  );
};

type CodeProps = PropsWithChildren<
  Pick<HTMLAttributes<HTMLElement>, "className">
> & {
  inline?: boolean;
};

export const Code = ({ children, className, ...rest }: CodeProps) => {
  const match = /language-(\w+)/.exec(className || "");
  const parsedChildren = parseChildrenTextContent(children);

  const { colorScheme } = useColorScheme();
  const syntaxHighlighterStyle = useMemo(
    () => (colorScheme === "dark" ? oneDark : oneLight),
    [colorScheme],
  );

  return match ? (
    <SyntaxHighlighter
      {...rest}
      PreTag="div" // intentional for styling purposes
      language={match[1]}
      showLineNumbers
      style={syntaxHighlighterStyle}
      codeTagProps={{ className: styles.code }}
      className={classNames(className, styles.code)}
    >
      {String(parsedChildren).replace(/\n$/, "")}
    </SyntaxHighlighter>
  ) : (
    <code {...rest} className={classNames(className, styles.code)}>
      {parsedChildren}
    </code>
  );
};
