import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { VitePWA } from "vite-plugin-pwa";

const apiProxyTarget = process.env.API_PROXY_TARGET || "http://localhost:8000";

export default defineConfig({
  plugins: [
    vue(),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["favicon.svg"],
      manifest: {
        name: "Firona",
        short_name: "Firona",
        description: "Radar des articles en tendance sur le marché malgache",
        theme_color: "#12241c",
        background_color: "#12241c",
        display: "standalone",
        start_url: "/",
        lang: "fr",
        icons: [
          {
            src: "favicon.svg",
            sizes: "512x512",
            type: "image/svg+xml",
            purpose: "any maskable",
          },
        ],
      },
    }),
  ],
  server: {
    host: true,
    port: 5173,
    proxy: {
      "/api": {
        target: apiProxyTarget,
        changeOrigin: true,
      },
    },
  },
});
