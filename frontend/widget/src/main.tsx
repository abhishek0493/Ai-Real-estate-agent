/**
 * Widget bootstrap — reads tenant key from the script tag,
 * creates a shadow-free container, and mounts the React widget.
 */
import React from "react";
import ReactDOM from "react-dom/client";
import Widget from "./components/Widget";
import { configure } from "./services/chatApi";
import "./index.css";

(function bootstrap() {
  // Find the script tag that loaded us
  const scripts = document.querySelectorAll("script[data-tenant-key]");
  const scriptTag = scripts[scripts.length - 1]; // last match

  const tenantKey = scriptTag?.getAttribute("data-tenant-key") || "";
  const apiBase =
    scriptTag?.getAttribute("data-api-url") || "http://localhost:8000/api/v1";

  if (!tenantKey) {
    console.warn("[AI-RE Widget] Missing data-tenant-key attribute on script tag.");
  }

  // Configure the API client
  configure(apiBase, tenantKey);

  // Create a container div
  const container = document.createElement("div");
  container.id = "ai-re-widget-root";
  document.body.appendChild(container);

  // Mount React
  const root = ReactDOM.createRoot(container);
  root.render(
    React.createElement(React.StrictMode, null, React.createElement(Widget))
  );
})();
