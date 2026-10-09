import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./App.css";
import { IS_WEB } from "./platform";

// On lolworlds.com the site-wide service worker serves every request cache-first, which would
// show stale live scores. /riftwatch/sw.js is a pass-through worker whose narrower scope wins.
if (IS_WEB && "serviceWorker" in navigator && window.location.pathname.startsWith("/riftwatch")) {
  navigator.serviceWorker.register("/riftwatch/sw.js", { scope: "/riftwatch/" }).catch(() => {});
}

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
