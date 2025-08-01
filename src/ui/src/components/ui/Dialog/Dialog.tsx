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

export interface DialogProps extends PropsWithChildren {
  title: string;
  trigger?: JSX.Element;
  footer?: ReactNode;
  isOpen?: boolean;
  isCentered?: boolean;
  hasPlainHeader?: boolean; // If true, the dialog header will have the same background color as the dialog content
  maxWidth?: number;
  onClose?: () => void;
  onOpenChange?: (isOpen: boolean) => void;
}

const Dialog = forwardRef<DialogRef, DialogProps>(
  (
    {
      title,
      isOpen,
      trigger,
      footer,
      maxWidth,
      isCentered,
      hasPlainHeader,
      onClose,
      onOpenChange,
      children,
      ...rest
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

    const dialogContent = (
      <Modal
        className="dialog"
        isDismissable
        isOpen={isOpen}
        onOpenChange={onOpenChange}
      >
        <div className={dialogWrapperClassName} style={{ maxWidth }}>
          <AriaDialog
            role="dialog"
            className="dialog__box"
            aria-labelledby={headingId}
            {...rest}
          >
            {({ close }) => {
              closeRef.current = close;

              const headerClassName = classNames("dialog__header", {
                "dialog__header--plain": hasPlainHeader,
              });

              return (
                <>
                  <header className={headerClassName}>
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
      </Modal>
    );

    if (!trigger) {
      return createPortal(dialogContent, document.body);
    }

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
                {...rest}
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
