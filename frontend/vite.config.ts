import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "path";

// https://vite.dev/config/
export default defineConfig({
  base: "",
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    proxy: {
      "/v1": {
        target: "http://127.0.0.1:8080",
        changeOrigin: true,
      },
    },
  },
  build: {
    commonjsOptions: {
      // Enable deterministic builds, as per https://github.com/vitejs/vite/issues/13672#issuecomment-1784110536
      strictRequires: true,
    },
    outDir: "../src/maia_ui/ui",
    emptyOutDir: true,
    rollupOptions: {
      output: {
        manualChunks: undefined,
        inlineDynamicImports: true,
        // Use static filenames instead of content hashes
        entryFileNames: "assets/index.js",
        chunkFileNames: "assets/[name].js",
        assetFileNames: "assets/[name].[ext]",
      },
    },
  },
});
