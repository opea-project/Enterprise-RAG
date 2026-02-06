// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useCallback, useState } from "react";

const PINNED_CHATS_STORAGE_KEY = "pinnedChats";

const getPinnedChatsFromStorage = (): string[] => {
  try {
    const pinned = localStorage.getItem(PINNED_CHATS_STORAGE_KEY);
    return pinned ? JSON.parse(pinned) : [];
  } catch {
    return [];
  }
};

const setPinnedChatsToStorage = (pinnedIds: string[]): void => {
  localStorage.setItem(PINNED_CHATS_STORAGE_KEY, JSON.stringify(pinnedIds));
};

export const usePinnedChats = () => {
  const [pinnedIds, setPinnedIds] = useState<string[]>(
    getPinnedChatsFromStorage,
  );

  const handleError = useCallback((message: string) => {
    console.error(`[usePinnedChats] ${message}`);
  }, []);

  const isPinned = useCallback(
    (id: string): boolean => {
      return pinnedIds.includes(id);
    },
    [pinnedIds],
  );

  const pinChat = useCallback(
    (id: string): void => {
      try {
        if (!pinnedIds.includes(id)) {
          const newPinnedIds = [id, ...pinnedIds];
          setPinnedChatsToStorage(newPinnedIds);
          setPinnedIds(newPinnedIds);
        }
      } catch {
        handleError("Failed to pin chat. Please try again.");
      }
    },
    [pinnedIds, handleError],
  );

  const unpinChat = useCallback(
    (id: string): void => {
      try {
        const newPinnedIds = pinnedIds.filter((pinnedId) => pinnedId !== id);
        setPinnedChatsToStorage(newPinnedIds);
        setPinnedIds(newPinnedIds);
      } catch {
        handleError("Failed to unpin chat. Please try again.");
      }
    },
    [pinnedIds, handleError],
  );

  const togglePinChat = useCallback(
    (id: string): void => {
      if (isPinned(id)) {
        unpinChat(id);
      } else {
        pinChat(id);
      }
    },
    [isPinned, pinChat, unpinChat],
  );

  return {
    pinnedIds,
    isPinned,
    pinChat,
    unpinChat,
    togglePinChat,
  };
};
