// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./DataIngestionTab.scss";

import { Button, CircularProgress, SelectChangeEvent } from "@mui/material";
import { useState } from "react";

import DataIngestionInfoAlert from "@/components/admin-panel/data-ingestion/DataIngestionInfoAlert/DataIngestionInfoAlert";
import DataSourceTypeSelect from "@/components/admin-panel/data-ingestion/DataSourceTypeSelect/DataSourceTypeSelect";
import DocumentsIngestionPanel from "@/components/admin-panel/data-ingestion/DocumentsIngestionPanel/DocumentsIngestionPanel";
import LinksIngestionPanel from "@/components/admin-panel/data-ingestion/LinksIngestionPanel/LinksIngestionPanel";
import NotificationSnackbar, {
  AppNotification,
} from "@/components/shared/NotificationSnackbar/NotificationSnackbar";
import {
  DataIngestionSourceType,
  LinkForIngestion,
} from "@/models/dataIngestion";
import DataIngestionService from "@/services/dataIngestionService";

const isUploadDataButtonDisabled = (
  documents: File[],
  links: LinkForIngestion[],
  isUploading: boolean,
) => isUploading || (documents.length === 0 && links.length === 0);

const DataIngestionTab = () => {
  const [selectedDataSourceType, setSelectedDataSourceType] =
    useState<DataIngestionSourceType>("documents");
  const [documents, setDocuments] = useState<File[]>([]);
  const [links, setLinks] = useState<LinkForIngestion[]>([]);
  const [uploadNotification, setUploadNotification] = useState<AppNotification>(
    {
      open: false,
      message: "",
      severity: "success",
    },
  );
  const [isUploading, setIsUploading] = useState(false);

  const handleDataSourceSelectChange = (
    event: SelectChangeEvent<DataIngestionSourceType>,
  ) => {
    setSelectedDataSourceType(event.target.value as DataIngestionSourceType);
  };

  const uploadDataButtonDisabled = isUploadDataButtonDisabled(
    documents,
    links,
    isUploading,
  );

  const submitUploadData = async () => {
    setIsUploading(true);

    const newUploadNotification: AppNotification = {
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

  const handleUploadNotificationClose = () => {
    setUploadNotification((prevNotification) => ({
      ...prevNotification,
      open: false,
    }));
  };

  return (
    <>
      <DataIngestionInfoAlert />
      <DataSourceTypeSelect
        value={selectedDataSourceType}
        onChange={handleDataSourceSelectChange}
      />
      <section className="selected-panel">
        {selectedDataSourceType === "documents" && (
          <DocumentsIngestionPanel
            documents={documents}
            setDocuments={setDocuments}
            disabled={isUploading}
          />
        )}
        {selectedDataSourceType === "links" && (
          <LinksIngestionPanel
            links={links}
            setLinks={setLinks}
            disabled={isUploading}
          />
        )}
      </section>
      <aside className="upload-data-panel">
        <Button
          disabled={uploadDataButtonDisabled}
          size="large"
          onClick={submitUploadData}
        >
          {isUploading ? (
            <>
              <CircularProgress
                size={20}
                className="uploading-circular-progress"
              />
              Uploading...
            </>
          ) : (
            "Upload Data"
          )}
        </Button>
      </aside>
      <NotificationSnackbar
        {...uploadNotification}
        onNotificationClose={handleUploadNotificationClose}
      />
    </>
  );
};

export default DataIngestionTab;
