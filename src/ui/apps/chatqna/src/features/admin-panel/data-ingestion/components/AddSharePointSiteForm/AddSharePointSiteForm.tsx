// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  Button,
  Popover,
  TextInput,
  usePopover,
} from "@intel-enterprise-rag-ui/components";
import { ErrorIcon, IconName } from "@intel-enterprise-rag-ui/icons";
import { ChangeEvent, useState } from "react";

import { usePostSharePointSiteMutation } from "@/features/admin-panel/data-ingestion/api/edpApi";
import { parseSharePointError } from "@/features/admin-panel/data-ingestion/utils";

interface AddSharePointSiteFormProps {
  onSiteAdded: () => void;
}

const AddSharePointSiteForm = ({ onSiteAdded }: AddSharePointSiteFormProps) => {
  const [siteUrl, setSiteUrl] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [postSharePointSite, { isLoading }] = usePostSharePointSiteMutation();

  const btnContent = isLoading ? "Adding..." : "Add Site";
  const btnIcon: IconName | undefined = isLoading ? "loading" : undefined;

  const handleSiteUrlChange = (event: ChangeEvent<HTMLInputElement>) => {
    setSiteUrl(event.target.value);
  };

  const handleAddSite = async () => {
    const trimmedUrl = siteUrl.trim();
    if (!trimmedUrl) return;

    try {
      new URL(trimmedUrl);
    } catch {
      setErrorMessage(
        "Invalid URL format. Please enter a valid SharePoint site URL.",
      );
      return;
    }

    setErrorMessage("");
    const { error } = await postSharePointSite({ site_url: trimmedUrl });

    if (error) {
      setErrorMessage(parseSharePointError(error));
    } else {
      setSiteUrl("");
      onSiteAdded();
    }
  };

  const { triggerRef, isOpen, togglePopover } = usePopover<HTMLDivElement>();

  return (
    <div className="sharepoint-sites-dialog__add-form">
      <TextInput
        data-testid="sharepoint-site-url-input"
        type="url"
        value={siteUrl}
        name="sharepoint-site-url"
        placeholder="Enter SharePoint site URL"
        className="w-full"
        onChange={handleSiteUrlChange}
      />
      <div className="sharepoint-sites-dialog__add-form-row">
        {errorMessage && (
          <>
            <div
              ref={triggerRef}
              className="sharepoint-sites-dialog__error-trigger"
              onClick={togglePopover}
            >
              <ErrorIcon className="sharepoint-sites-dialog__error-trigger--icon" />
              <p className="sharepoint-sites-dialog__error-trigger--text">
                Error adding site
              </p>
            </div>
            <Popover
              data-testid="sharepoint-error-popover"
              isOpen={isOpen}
              triggerRef={triggerRef}
              placement="bottom end"
              ariaLabel="SharePoint Error"
              onOpenChange={togglePopover}
            >
              <section className="sharepoint-sites-dialog__error-section">
                {errorMessage}
              </section>
            </Popover>
          </>
        )}
        <Button
          data-testid="add-sharepoint-site-button"
          icon={btnIcon}
          isDisabled={!siteUrl.trim() || isLoading}
          onPress={handleAddSite}
        >
          {btnContent}
        </Button>
      </div>
    </div>
  );
};

export default AddSharePointSiteForm;
