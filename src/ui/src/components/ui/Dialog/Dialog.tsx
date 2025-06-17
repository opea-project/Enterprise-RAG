// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./Dialog.scss";

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
  Pressable,
} from "react-aria-components";
import { createPortal } from "react-dom";

import IconButton from "@/components/ui/IconButton/IconButton";

export interface DialogRef {
  close: () => void;
}

interface DialogProps extends PropsWithChildren {
  trigger: JSX.Element;
  footer?: ReactNode;
  title: string;
  onClose?: () => void;
}

const Dialog = forwardRef<DialogRef, DialogProps>(
  (
    { trigger, footer, title, onClose, children, ...restProps }: DialogProps,
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

    return (
      <DialogTrigger>
        <Pressable>{trigger}</Pressable>
        {createPortal(
          <Modal className="dialog" isDismissable>
            <div className="dialog__wrapper">
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
                      <Heading
                        slot="title"
                        className="dialog__header"
                        id={headingId}
                      >
                        <h3>{title}</h3>
                        <IconButton
                          icon="close"
                          aria-label="Close dialog"
                          onPress={() => {
                            onClose?.();
                            close();
                          }}
                        />
                      </Heading>
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
