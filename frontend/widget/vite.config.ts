import { defineConfig, Plugin } from "vite";
import react from "@vitejs/plugin-react";
import { readFileSync } from "fs";
import { resolve } from "path";

// Plugin to inject CSS into JS as a <style> tag at runtime
function cssInjectPlugin(): Plugin {
  return {
    name: "css-inject",
    enforce: "post",
    generateBundle(_, bundle) {
      let cssContent = "";
      // Find and remove CSS chunks
      for (const key of Object.keys(bundle)) {
        if (key.endsWith(".css")) {
          const chunk = bundle[key];
          if (chunk.type === "asset" && typeof chunk.source === "string") {
            cssContent += chunk.source;
          }
          delete bundle[key];
        }
      }
      // Inject CSS into JS chunks
      if (cssContent) {
        const injection = `(function(){var s=document.createElement("style");s.textContent=${JSON.stringify(cssContent)};document.head.appendChild(s)})();`;
        for (const key of Object.keys(bundle)) {
          const chunk = bundle[key];
          if (chunk.type === "chunk" && chunk.isEntry) {
            chunk.code = injection + chunk.code;
          }
        }
      }
    },
  };
}

export default defineConfig({
  plugins: [react(), cssInjectPlugin()],
  define: {
    "process.env.NODE_ENV": JSON.stringify("production"),
  },
  build: {
    lib: {
      entry: "src/main.tsx",
      name: "AIRealEstateWidget",
      fileName: () => "widget.js",
      formats: ["iife"],
    },
    rollupOptions: {
      // Bundle everything into a single file — no external deps
    },
    cssCodeSplit: false,
    minify: "esbuild",
  },
});
