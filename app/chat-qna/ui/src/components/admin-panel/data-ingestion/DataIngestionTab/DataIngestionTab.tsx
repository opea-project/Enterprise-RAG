// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./DataIngestionTab.scss";

import { useState } from "react";

import DataIngestionUploadPanel from "@/components/admin-panel/data-ingestion/DataIngestionUploadPanel/DataIngestionUploadPanel";
import DocumentsIngestionPanel from "@/components/admin-panel/data-ingestion/DocumentsIngestionPanel/DocumentsIngestionPanel";
import LinksIngestionPanel from "@/components/admin-panel/data-ingestion/LinksIngestionPanel/LinksIngestionPanel";
import NotificationToast, {
  Notification,
} from "@/components/shared/NotificationToast/NotificationToast";
import { LinkForIngestion } from "@/models/admin-panel/data-ingestion/dataIngestion";
import DataIngestionService from "@/services/dataIngestionService";

const DataIngestionTab = () => {
  const [documents, setDocuments] = useState<File[]>([]);
  const [links, setLinks] = useState<LinkForIngestion[]>([]);
  const [uploadNotification, setUploadNotification] = useState<Notification>({
    open: false,
    message: "",
    severity: "success",
  });
  const [isUploading, setIsUploading] = useState(false);

  const submitUploadData = async () => {
    setIsUploading(true);

    const newUploadNotification: Notification = {
      open: true,
      message: "",
      severity: "success",
    };
    try {
      const response = await DataIngestionService.postDataToIngest(
        documents,
        links,
      );

      if (response.ok) {
        newUploadNotification.message = "Successful data upload!";
      } else {
        newUploadNotification.message = "Error occurred during upload";
        newUploadNotification.severity = "error";
      }
    } catch (e) {
      if (e instanceof Error) {
        newUploadNotification.message = e.message;
        newUploadNotification.severity = "error";
        throw new Error(e.message);
      } else {
        throw new Error();
      }
    } finally {
      setUploadNotification(newUploadNotification);
      setIsUploading(false);

      if (newUploadNotification.severity === "success") {
        setDocuments([]);
        setLinks([]);
      }
    }
  };

  const hideNotification = () => {
    setUploadNotification((prevNotification) => ({
      ...prevNotification,
      open: false,
    }));
  };

  return (
    <>
      <div className="data-ingestion-panel">
        <DocumentsIngestionPanel
          documents={documents}
          setDocuments={setDocuments}
          disabled={isUploading}
        />
        <LinksIngestionPanel
          links={links}
          setLinks={setLinks}
          disabled={isUploading}
        />
      </div>
      <DataIngestionUploadPanel
        documents={documents}
        links={links}
        isUploading={isUploading}
        onUploadBtnClick={submitUploadData}
      />
      <NotificationToast
        {...uploadNotification}
        hideNotification={hideNotification}
      />
    </>
  );
};

export default DataIngestionTab;
