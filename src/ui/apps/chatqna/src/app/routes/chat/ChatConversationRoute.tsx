// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  ChatConversationLayout,
  ChatSideMenu,
  selectIsChatSideMenuOpen,
  useChat,
  useChatHistoryHandlers,
} from "@intel-enterprise-rag-ui/chat";
import { addNotification } from "@intel-enterprise-rag-ui/components";
import { PageLayout } from "@intel-enterprise-rag-ui/layouts";
import { downloadBlob } from "@intel-enterprise-rag-ui/utils";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";

import {
  useGetFilePresignedUrlMutation,
  useLazyDownloadFileQuery,
} from "@/api";
import {
  AppHeaderLeftSideContent,
  AppHeaderRightSideContent,
} from "@/components/AppHeaderContent/AppHeaderContent";

import { paths } from "@/config/paths";
import {
  useChangeChatNameMutation,
  useDeleteChatMutation,
  useGetAllChatsQuery,
  useLazyGetAllChatsQuery,
  useLazyGetChatByIdQuery,
  useSaveChatMutation,
} from "@/features/chat/api/chatHistory.api";
import { usePostPromptMutation } from "@/features/chat/api/chatQnA.api";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { setLastSelectedChatId } from "@/store/viewNavigation.slice";
import { getChatQnAAppEnv } from "@/utils";

const MAINTENANCE_MODE = getChatQnAAppEnv("MAINTENANCE_MODE");

const ChatConversationRoute = () => {
  // React store, RTK Query, and react-router hooks
  const navigate = useNavigate();
  const { chatId: chatIdFromParams } = useParams<{ chatId?: string }>();
  const dispatch = useAppDispatch();
  const location = useLocation();
  const isChatSideMenuOpen = useAppSelector(selectIsChatSideMenuOpen);
  const { data: chatHistoryData, isLoading: isLoadingChatHistory } =
    useGetAllChatsQuery();
  const [downloadFile] = useLazyDownloadFileQuery();
  const [getFilePresignedUrl] = useGetFilePresignedUrlMutation();

  // Custom hooks from chat package
  const {
    userInput,
    chatTurns,
    isChatResponsePending,
    onNewChat,
    onPromptChange,
    onPromptSubmit,
    onRequestAbort,
  } = useChat({
    usePostPromptMutation,
    useGetAllChatsQuery,
    useLazyGetChatByIdQuery,
    streamingConfig: {
      dispatch,
      useSaveChatMutation,
      useLazyGetChatByIdQuery,
    },
    useAppSelector,
    currentChatId: chatIdFromParams,
    isChatSideMenuOpen,
    onNavigate: (path) => navigate(path),
    onNavigateToChat: (chatId) => navigate(`${paths.chat}/${chatId}`),
    onChatIdChange: (chatId) => dispatch(setLastSelectedChatId(chatId)),
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

  const chatDisclaimer = getChatQnAAppEnv("CHAT_DISCLAIMER_TEXT") ?? "";

  const handleFileDownload = async (fileName: string, bucketName: string) => {
    const { data: presignedUrl } = await getFilePresignedUrl({
      fileName,
      method: "GET",
      bucketName,
    });

    if (presignedUrl) {
      downloadFile({ presignedUrl, fileName });
    }
  };

  if (MAINTENANCE_MODE === "true") {
    return (
      <PageLayout
        appHeaderProps={{
          leftSideContent: <AppHeaderLeftSideContent />,
          rightSideContent: <AppHeaderRightSideContent />,
        }}
      >
        <div className="flex h-screen flex-col items-center justify-center p-8 text-center">
          <h2>Maintenance Mode</h2>
          <p>
            The Chat QnA application is currently under maintenance.
            
 Only <Link to="/admin-panel">Admin Panel</Link> is
            accessible. Please check back later.
          </p>
        </div>
      </PageLayout>
    );
  }

  return (
    <PageLayout
      appHeaderProps={{
        leftSideContent: <AppHeaderLeftSideContent />,
        rightSideContent: <AppHeaderRightSideContent onNewChat={onNewChat} />,
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
      <ChatConversationLayout
        userInput={userInput}
        conversationTurns={chatTurns}
        isChatResponsePending={isChatResponsePending}
        disclaimer={chatDisclaimer}
        onPromptChange={onPromptChange}
        onPromptSubmit={onPromptSubmit}
        onRequestAbort={onRequestAbort}
        onFileDownload={handleFileDownload}
      />
    </PageLayout>
  );
};

export default ChatConversationRoute;