// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  ChatConversationLayout,
  ChatSideMenu,
  InitialChatLayout,
  selectIsChatSideMenuOpen,
  useChatHistoryHandlers,
  useInitialChat,
} from "@intel-enterprise-rag-ui/chat";
import { addNotification } from "@intel-enterprise-rag-ui/components";
import { PageLayout } from "@intel-enterprise-rag-ui/layouts";
import { downloadBlob } from "@intel-enterprise-rag-ui/utils";
import { useLocation, useNavigate } from "react-router-dom";

import {
  useGetFilePresignedUrlMutation,
  useLazyDownloadFileQuery,
} from "@/api";
import {
  AppHeaderLeftSideContent,
  AppHeaderRightSideContent,
} from "@/components/AppHeaderContent/AppHeaderContent";
import { paths } from "@/config/paths";
import { usePostSharePointFileUrlMutation } from "@/features/admin-panel/data-ingestion/api/edpApi";
import { usePostPromptMutation } from "@/features/chat/api/audioQnA.api";
import {
  useChangeChatNameMutation,
  useDeleteChatMutation,
  useGetAllChatsQuery,
  useLazyGetAllChatsQuery,
  useLazyGetChatByIdQuery,
  useSaveChatMutation,
} from "@/features/chat/api/chatHistory.api";
import { useTextToSpeech } from "@/features/chat/hooks/useTextToSpeech";
import { useSpeechToTextHandlers } from "@/hooks/useSpeechToTextHandlers";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { getAudioQnAAppEnv } from "@/utils";

const InitialChatRoute = () => {
  // React store, RTK Query, and react-router hooks
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const location = useLocation();
  const isChatSideMenuOpen = useAppSelector(selectIsChatSideMenuOpen);
  const { data: chatHistoryData, isLoading: isLoadingChatHistory } =
    useGetAllChatsQuery();
  const [downloadFile] = useLazyDownloadFileQuery();
  const [getFilePresignedUrl] = useGetFilePresignedUrlMutation();
  const [postSharePointFileUrl] = usePostSharePointFileUrlMutation();

  // Custom hook for ASR handlers
  const { handleSpeechToText, handleSpeechToTextError } =
    useSpeechToTextHandlers();

  // Custom hooks from chat package
  const {
    userInput,
    chatTurns,
    isChatResponsePending,
    onPromptChange,
    onPromptSubmit,
    onRequestAbort,
  } = useInitialChat({
    usePostPromptMutation,
    streamingConfig: {
      dispatch,
      useSaveChatMutation,
      useLazyGetChatByIdQuery,
    },
    isChatSideMenuOpen,
    onNavigateToChat: (chatId) => navigate(`${paths.chat}/${chatId}`),
  });

  const {
    handleItemPress,
    isItemActive,
    handleDelete,
    handleExport,
    handleRename,
  } = useChatHistoryHandlers({
    chatHistoryData,
    useDeleteChatMutation,
    useLazyGetAllChatsQuery,
    useLazyGetChatByIdQuery,
    useChangeChatNameMutation,
    dispatch,
    location,
    navigate,
    chatBasePath: paths.chat,
    onDeleteError: (error) => {
      dispatch(
        addNotification({
          severity: "error",
          text: `Failed to delete chat history: ${error.message}`,
        }),
      );
    },
    onRenameError: (error) => {
      dispatch(
        addNotification({
          severity: "error",
          text: `Failed to rename chat: ${error.message}`,
        }),
      );
    },
    onExportSuccess: (blob, fileName) => {
      downloadBlob(blob, fileName);
    },
  });

  const { playingTurnId, playingState, onPlayMessage } = useTextToSpeech();

  const chatDisclaimer = getAudioQnAAppEnv("CHAT_DISCLAIMER_TEXT") ?? "";

  const handleFileDownload = async (
    fileName: string,
    bucketName: string | null,
    siteName: string | null,
  ) => {
    if (siteName) {
      const { data } = await postSharePointFileUrl({
        site_name: siteName,
        object_name: fileName,
      });
      if (data?.url) {
        window.open(data.url, "_blank", "noopener,noreferrer");
      }
      return;
    }

    if (!bucketName) return;

    const { data: presignedUrl } = await getFilePresignedUrl({
      fileName,
      method: "GET",
      bucketName,
    });

    if (presignedUrl) {
      downloadFile({ presignedUrl, fileName });
    }
  };

  const getChatLayout = () => {
    if (chatTurns.length === 0) {
      return (
        <InitialChatLayout
          userInput={userInput}
          disclaimer={chatDisclaimer}
          onPromptChange={onPromptChange}
          onPromptSubmit={onPromptSubmit}
          onSpeechToText={handleSpeechToText}
          onSpeechToTextError={handleSpeechToTextError}
          enableMicrophone
        />
      );
    }

    return (
      <ChatConversationLayout
        userInput={userInput}
        conversationTurns={chatTurns}
        isChatResponsePending={isChatResponsePending}
        disclaimer={chatDisclaimer}
        playingTurnId={playingTurnId}
        playingState={playingState}
        onPromptChange={onPromptChange}
        onPromptSubmit={onPromptSubmit}
        onRequestAbort={onRequestAbort}
        onFileDownload={handleFileDownload}
        onPlayMessage={onPlayMessage}
        onSpeechToText={handleSpeechToText}
        onSpeechToTextError={handleSpeechToTextError}
        enableMicrophone
      />
    );
  };

  return (
    <PageLayout
      appHeaderProps={{
        leftSideContent: <AppHeaderLeftSideContent />,
        rightSideContent: <AppHeaderRightSideContent />,
      }}
      leftSideMenu={{
        component: (
          <ChatSideMenu
            isOpen={isChatSideMenuOpen}
            chatHistoryData={chatHistoryData}
            isLoadingChatHistory={isLoadingChatHistory}
            onItemPress={handleItemPress}
            isItemActive={isItemActive}
            onDelete={handleDelete}
            onExport={handleExport}
            onRename={handleRename}
          />
        ),
        isOpen: isChatSideMenuOpen,
      }}
    >
      {getChatLayout()}
    </PageLayout>
  );
};

export default InitialChatRoute;
