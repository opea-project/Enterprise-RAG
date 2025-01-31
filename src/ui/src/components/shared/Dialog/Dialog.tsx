// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./Dialog.scss";

import { forwardRef, PropsWithChildren, ReactNode } from "react";
import { createPortal } from "react-dom";

import IconButton from "@/components/shared/IconButton/IconButton";

export interface DialogProps extends PropsWithChildren {
  trigger: ReactNode;
  footer?: ReactNode;
  title: string;
  onClose: () => void;
}

const Dialog = forwardRef<HTMLDialogElement, DialogProps>(
  ({ trigger, footer, title, onClose, children }: DialogProps, ref) => (
    <>
      {trigger}
      {createPortal(
        <dialog ref={ref}>
          <div className="dialog__box">
            <header className="dialog__header">
              <h3>{title}</h3>
              <IconButton icon="close" onClick={onClose} />
            </header>
            <section className="dialog__content">{children}</section>
            {footer && <footer className="dialog__actions">{footer}</footer>}
          </div>
        </dialog>,
        document.getElementsByClassName("admin-panel")[0]!,
      )}
    </>
  ),
);

export default Dialog;
