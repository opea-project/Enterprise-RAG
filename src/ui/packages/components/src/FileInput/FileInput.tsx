// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./FileInput.scss";

import { Button } from "@intel-enterprise-rag-ui/components";
import { FileIcon } from "@intel-enterprise-rag-ui/icons";
import classNames from "classnames";
import {
  DragEvent,
  forwardRef,
  Fragment,
  InputHTMLAttributes,
  useCallback,
  useImperativeHandle,
  useMemo,
  useRef,
  useState,
} from "react";

export interface FileInputHandle {
  clear: () => void;
  click: () => void;
}

interface FileInputProps extends InputHTMLAttributes<HTMLInputElement> {
  /* Array of supported file extensions. If defined, a proper message will be displayed.  */
  supportedFileExtensions?: string[];
  /* A limit of upload in MB. If defined, a proper message will be displayed. */
  totalSizeLimit?: number;
  /* Error message to be displayed. */
  errorMessage?: string;
}

export const FileInput = forwardRef<FileInputHandle, FileInputProps>(
  (
    {
      errorMessage,
      totalSizeLimit,
      supportedFileExtensions,
      multiple = false,
      onDrop,
      onChange,
      className,
      ...rest
    }: FileInputProps,
    forwardedRef,
  ) => {
    const fileInputRef = useRef<HTMLInputElement | null>(null);
    useImperativeHandle(forwardedRef, () => ({
      clear: () => {
        if (fileInputRef.current) {
          fileInputRef.current.value = "";
        }
      },
      click: () => {
        fileInputRef.current?.click();
      },
    }));

    const [isDragOver, setIsDragOver] = useState(false);

    const handleFileInputDragOver = useCallback((event: DragEvent) => {
      event.preventDefault();
      setIsDragOver(true);
    }, []);

    const handleFileInputDragLeave = useCallback(() => {
      setIsDragOver(false);
    }, []);

    const handleDrop = useCallback(
      (event: DragEvent<HTMLInputElement>) => {
        setIsDragOver(false);
        onDrop?.(event);
      },
      [onDrop],
    );

    const handleBrowseFilesButtonPress = useCallback(() => {
      fileInputRef.current!.click();
    }, []);

    const fileInputBoxClassNames = classNames("file-input__box", {
      "file-input__box--drag-over": isDragOver,
    });

    const fileInputAccept = useMemo(
      () =>
        supportedFileExtensions
          ? supportedFileExtensions
              .map((extension) => `.${extension}`)
              .join(",")
          : undefined,
      [supportedFileExtensions],
    );

    const supportedFileFormatsMsg = useMemo(
      () =>
        supportedFileExtensions
          ? `Supported file formats:  ${supportedFileExtensions
              .map((extension) => extension.toUpperCase())
              .join(", ")}`
          : "",
      [supportedFileExtensions],
    );

    const hasErrorMessage = useMemo(
      () => errorMessage && errorMessage !== "",
      [errorMessage],
    );

    const ariaLabel = useMemo(() => {
      if (rest["aria-label"]) {
        return rest["aria-label"];
      }
      if (multiple) {
        return "File Input, multiple files enabled";
      }
      return "File Input";
    }, [multiple, rest]);

    return (
      <div className={className}>
        <div
          className={fileInputBoxClassNames}
          onDragOver={handleFileInputDragOver}
          onDragLeave={handleFileInputDragLeave}
          onDrop={handleDrop}
        >
          {!isDragOver && (
            <>
              <FileIcon fontSize={20} />
              <p>Drag and Drop File{multiple && "s"}</p>
              <p className="file-input__box__caption">or</p>
              <Button size="sm" onPress={handleBrowseFilesButtonPress}>
                Browse Files
              </Button>
              {totalSizeLimit && (
                <p className="file-input__box__caption">{`Single upload size limit: ${totalSizeLimit}MB`}</p>
              )}
            </>
          )}
          {isDragOver && <p>Drop Here</p>}
          <input
            {...rest}
            ref={fileInputRef}
            type="file"
            accept={fileInputAccept}
            className="file-input__box__input"
            multiple={multiple}
            aria-label={ariaLabel}
            onChange={onChange}
          />
        </div>
        {hasErrorMessage && (
          <p className="file-input__error-message">
            {(errorMessage ?? "").split("\n").map((msg, index) => (
              <Fragment key={`file-input-error-msg-${index}`}>
                {msg}
                <br />
              </Fragment>
            ))}
          </p>
        )}
        {supportedFileFormatsMsg && (
          <p className="file-input__supported-formats-message">
            {supportedFileFormatsMsg}
          </p>
        )}
      </div>
    );
  },
);

FileInput.displayName = "FileInput";
