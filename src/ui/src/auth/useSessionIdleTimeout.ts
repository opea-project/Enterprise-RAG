// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useEffect, useRef } from "react";

import keycloakService from "@/services/keycloakService";

const SESSION_IDLE_TIMEOUT = import.meta.env.VITE_SESSION_IDLE_TIMEOUT * 1000; // to milliseconds

const useSessionIdleTimeout = () => {
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const resetSessionIdleTimeout = () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      timeoutRef.current = setTimeout(() => {
        console.info("Session idle timeout. Logging out.");
        keycloakService.logout();
      }, SESSION_IDLE_TIMEOUT);
    };

    resetSessionIdleTimeout();

    const events = [
      "mousemove",
      "mousedown",
      "mouseup",
      "click",
      "dblclick",
      "wheel",
      "keydown",
      "keyup",
      "keypress",
      "touchstart",
      "touchmove",
      "touchend",
      "resize",
      "scroll",
      "focus",
      "blur",
      "input",
      "change",
      "load",
    ];

    events.forEach((event) =>
      window.addEventListener(event, resetSessionIdleTimeout),
    );

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      events.forEach((event) =>
        window.removeEventListener(event, resetSessionIdleTimeout),
      );
    };
  }, []);
};

export default useSessionIdleTimeout;
