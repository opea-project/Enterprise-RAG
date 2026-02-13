// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

/**
 * Converts an audio blob to WAV format using Web Audio API
 * @param audioBlob - The audio blob to convert
 * @returns Promise resolving to a WAV formatted blob
 */
export const convertToWav = async (audioBlob: Blob): Promise<Blob> => {
  try {
    const AudioContextClass =
      window.AudioContext ||
      (window as unknown as { webkitAudioContext: typeof AudioContext })
        .webkitAudioContext;
    const audioContext = new AudioContextClass();

    const arrayBuffer = await audioBlob.arrayBuffer();

    const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);

    const wavBlob = audioBufferToWav(audioBuffer);

    await audioContext.close();

    return wavBlob;
  } catch (error) {
    console.error("Error converting audio to WAV:", error);
    throw new Error("Failed to convert audio to WAV format");
  }
};

/**
 * Converts an AudioBuffer to a WAV blob
 * @param audioBuffer - The AudioBuffer to convert
 * @returns WAV formatted blob
 */
const audioBufferToWav = (audioBuffer: AudioBuffer): Blob => {
  const numberOfChannels = audioBuffer.numberOfChannels;
  const sampleRate = audioBuffer.sampleRate;
  const format = 1; // PCM
  const bitDepth = 16;

  // Interleave channels
  const length = audioBuffer.length * numberOfChannels * 2;
  const buffer = new ArrayBuffer(44 + length);
  const view = new DataView(buffer);

  // Write WAV header
  writeString(view, 0, "RIFF");
  view.setUint32(4, 36 + length, true);
  writeString(view, 8, "WAVE");
  writeString(view, 12, "fmt ");
  view.setUint32(16, 16, true); // fmt chunk size
  view.setUint16(20, format, true);
  view.setUint16(22, numberOfChannels, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * numberOfChannels * (bitDepth / 8), true); // byte rate
  view.setUint16(32, numberOfChannels * (bitDepth / 8), true); // block align
  view.setUint16(34, bitDepth, true);
  writeString(view, 36, "data");
  view.setUint32(40, length, true);

  // Write interleaved audio data
  const channels: Float32Array[] = [];
  for (let i = 0; i < numberOfChannels; i++) {
    channels.push(audioBuffer.getChannelData(i));
  }

  let offset = 44;
  for (let i = 0; i < audioBuffer.length; i++) {
    for (let channel = 0; channel < numberOfChannels; channel++) {
      const sample = Math.max(-1, Math.min(1, channels[channel][i]));
      view.setInt16(
        offset,
        sample < 0 ? sample * 0x8000 : sample * 0x7fff,
        true,
      );
      offset += 2;
    }
  }

  return new Blob([buffer], { type: "audio/wav" });
};

/**
 * Helper function to write a string to a DataView
 */
const writeString = (view: DataView, offset: number, string: string): void => {
  for (let i = 0; i < string.length; i++) {
    view.setUint8(offset + i, string.charCodeAt(i));
  }
};
