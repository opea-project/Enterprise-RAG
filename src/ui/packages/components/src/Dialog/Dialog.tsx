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
  DialogTrigger as AriaDialogTrigger,
  Heading as AriaHeading,
  Modal as AriaModal,
} from "react-aria-components";
import { createPortal } from "react-dom";

import { IconButton } from "@/IconButton/IconButton";

export interface DialogRef {
  close: () => void;
}

export interface DialogProps extends PropsWithChildren {
  /** Title of the dialog */
  title: string;
  /** Element that triggers the dialog */
  trigger?: JSX.Element;
  /** Footer content for the dialog */
  footer?: ReactNode;
  /** If true, dialog is open */
  isOpen?: boolean;
  /** If true, dialog is centered */
  isCentered?: boolean;
  /** If true, header has same background as content */
  hasPlainHeader?: boolean;
  /** Maximum width of the dialog */
  maxWidth?: number;
  /** Callback when dialog is closed */
  onClose?: () => void;
  /** Callback when open state changes */
  onOpenChange?: (isOpen: boolean) => void;
}

/**
 * Dialog component for displaying modal dialogs with customizable header, footer, and content.
 */
export const Dialog = forwardRef<DialogRef, DialogProps>(
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
      <AriaModal
        className="dialog"
        isOpen={isOpen}
        onOpenChange={onOpenChange}
        isDismissable
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
                    <AriaHeading slot="title" id={headingId}>
                      {title}
                    </AriaHeading>
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
      </AriaModal>
    );

    if (!trigger) {
      return createPortal(dialogContent, document.body);
    }

    return (
      <AriaDialogTrigger>
        {trigger}
        {createPortal(
          <AriaModal className="dialog" isDismissable>
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
                        <AriaHeading slot="title" id={headingId}>
                          {title}
                        </AriaHeading>
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
          </AriaModal>,
          document.body,
        )}
      </AriaDialogTrigger>
    );
  },
);

Dialog.displayName = "Dialog";
