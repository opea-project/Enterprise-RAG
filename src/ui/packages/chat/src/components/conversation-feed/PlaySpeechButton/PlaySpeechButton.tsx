// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { IconButton, Tooltip } from "@intel-enterprise-rag-ui/components";
import { IconName } from "@intel-enterprise-rag-ui/icons";
import classNames from "classnames";

export type PlaySpeechButtonState = "idle" | "waiting" | "playing";

interface PlaySpeechButtonProps {
  /** Turn ID for the message */
  turnId: string;
  /** Current playing state */
  playingState: PlaySpeechButtonState;
  /** Callback when play is triggered */
  onPlayMessage: (turnId: string) => Promise<void>;
}

/**
 * Play speech button component for converting text to speech and playing audio.
 */
export const PlaySpeechButton = ({
  turnId,
  playingState,
  onPlayMessage,
}: PlaySpeechButtonProps) => {
  const handlePress = () => {
    if (playingState !== "idle") {
      return;
    }

    onPlayMessage(turnId);
  };

  const label =
    playingState === "idle"
      ? "Read aloud"
      : playingState === "waiting"
        ? "Generating audio..."
        : "Playing...";
  const icon: IconName = playingState === "waiting" ? "loading" : "speaker";
  const isDisabled = playingState !== "idle";

  const iconClassName = classNames({
    "animate-spin": playingState === "waiting",
  });

  return (
    <Tooltip
      title={label}
      placement="bottom"
      aria-label={label}
      trigger={
        <IconButton
          data-testid={`play-speech-button-${turnId}`}
          icon={icon}
          iconClassName={iconClassName}
          isDisabled={isDisabled}
          size="sm"
          onPress={handlePress}
        />
      }
    />
  );
};
