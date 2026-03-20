// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ChatHistoryItemData } from "@/types";

export type TimeCategory = "Today" | "Last 7 Days" | "Last 30 Days" | "Older";

export interface GroupedChatHistory {
  label: TimeCategory;
  items: ChatHistoryItemData[];
}

const TIME_CATEGORY_ORDER: TimeCategory[] = [
  "Today",
  "Last 7 Days",
  "Last 30 Days",
  "Older",
];

function getTimeCategory(dateStr: string, now: Date): TimeCategory {
  const date = new Date(dateStr);

  const startOfToday = new Date(
    now.getFullYear(),
    now.getMonth(),
    now.getDate(),
  );

  if (date >= startOfToday) return "Today";

  const daysAgo7 = new Date(startOfToday);
  daysAgo7.setDate(daysAgo7.getDate() - 7);
  if (date >= daysAgo7) return "Last 7 Days";

  const daysAgo30 = new Date(startOfToday);
  daysAgo30.setDate(daysAgo30.getDate() - 30);
  if (date >= daysAgo30) return "Last 30 Days";

  return "Older";
}

export function groupChatsByTime(
  items: ChatHistoryItemData[],
): GroupedChatHistory[] {
  const now = new Date();
  const grouped = new Map<TimeCategory, ChatHistoryItemData[]>();

  const sorted = [...items].sort(
    (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime(),
  );

  for (const item of sorted) {
    const category = getTimeCategory(item.createdAt, now);
    const group = grouped.get(category);
    if (group) {
      group.push(item);
    } else {
      grouped.set(category, [item]);
    }
  }

  return TIME_CATEGORY_ORDER.filter((label) => grouped.has(label)).map(
    (label) => ({
      label,
      items: grouped.get(label)!,
    }),
  );
}
