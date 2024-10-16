// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./AppHeader.scss";

import { useEffect, useState } from "react";
import {
  BsBoxArrowRight,
  BsChatLeftTextFill,
  BsDatabaseFillGear,
  BsMoonFill,
  BsSunFill,
} from "react-icons/bs";
import { useLocation, useNavigate } from "react-router-dom";

import Tooltip from "@/components/shared/Tooltip/Tooltip";
import keycloakService from "@/services/keycloakService";

const getThemeMode = () => localStorage.getItem("theme") === "dark";
const AppHeader = () => {
  const [dark, setDark] = useState(() => getThemeMode());
  useEffect(() => {
    if (dark) {
      document.body.classList.add("dark");
      localStorage.setItem("theme", "dark");
    } else {
      document.body.classList.remove("dark");
      localStorage.setItem("theme", "light");
    }
  }, [dark]);

  const handleToggleModeBtnClick = () => {
    setDark(!dark);
  };

  const navigate = useNavigate();
  const location = useLocation();
  const username = keycloakService.getUsername();

  const isAdmin = keycloakService.isAdmin();
  const isChatPage = location.pathname === "/chat";

  return (
    <header className="app-header">
      <div className="app-header__actions">
        <p className="app-header__app-name">Enterprise RAG</p>
      </div>
      <div className="app-header__actions">
        <p className="app-header__username">{username}</p>
        {isAdmin &&
          (isChatPage ? (
            <Tooltip text="Admin Panel">
              <button
                className="icon-button"
                onClick={() => navigate("/admin-panel")}
              >
                <BsDatabaseFillGear />
              </button>
            </Tooltip>
          ) : (
            <Tooltip text="Chat">
              <button className="icon-button" onClick={() => navigate("/chat")}>
                <BsChatLeftTextFill />
              </button>
            </Tooltip>
          ))}
        <Tooltip text={dark ? "Light Mode" : "Dark Mode"}>
          <button className="icon-button" onClick={handleToggleModeBtnClick}>
            {dark ? <BsSunFill /> : <BsMoonFill />}
          </button>
        </Tooltip>
        <Tooltip text="Logout" position="bottom-end">
          <button className="icon-button" onClick={keycloakService.logout}>
            <BsBoxArrowRight />
          </button>
        </Tooltip>
      </div>
    </header>
  );
};

export default AppHeader;
