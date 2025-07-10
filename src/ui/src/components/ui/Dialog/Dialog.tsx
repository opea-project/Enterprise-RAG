// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./Dialog.scss";

import classNames from "classnames";
import {
  forwardRef,
  PropsWithChildren,
  ReactNode,
  useId,
  useImperativeHandle,
  useRef,
} from "react";
import {
  Dialog as AriaDialog,
  DialogTrigger,
  Heading,
  Modal,
} from "react-aria-components";
import { createPortal } from "react-dom";

import IconButton from "@/components/ui/IconButton/IconButton";

export interface DialogRef {
  close: () => void;
}

interface DialogProps extends PropsWithChildren {
  trigger: JSX.Element;
  title: string;
  footer?: ReactNode;
  maxWidth?: number;
  isCentered?: boolean;
  onClose?: () => void;
}

const Dialog = forwardRef<DialogRef, DialogProps>(
  (
    {
      trigger,
      title,
      footer,
      maxWidth,
      isCentered,
      onClose,
      children,
      ...restProps
    }: DialogProps,
    forwardedRef,
  ) => {
    const closeRef = useRef<(() => void) | null>(null);

    useImperativeHandle(
      forwardedRef,
      () => ({
        close: () => closeRef.current?.(),
      }),
      [],
    );

    const headingId = useId();

    const dialogWrapperClassName = classNames("dialog__wrapper", {
      "dialog__wrapper--centered": isCentered,
    });

    return (
      <DialogTrigger>
        {trigger}
        {createPortal(
          <Modal className="dialog" isDismissable>
            <div className={dialogWrapperClassName} style={{ maxWidth }}>
              <AriaDialog
                role="dialog"
                className="dialog__box"
                aria-labelledby={headingId}
                {...restProps}
              >
                {({ close }) => {
                  closeRef.current = close;
                  return (
                    <>
                      <header className="dialog__header">
                        <Heading slot="title" id={headingId}>
                          {title}
                        </Heading>
                        <IconButton
                          icon="close"
                          aria-label="Close dialog"
                          onPress={() => {
                            onClose?.();
                            close();
                          }}
                        />
                      </header>
                      <section className="dialog__content">{children}</section>
                      {footer && (
                        <footer className="dialog__actions">{footer}</footer>
                      )}
                    </>
                  );
                }}
              </AriaDialog>
            </div>
          </Modal>,
          document.body,
        )}
      </DialogTrigger>
    );
  },
);

export default Dialog;
