import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { VitePWA } from "vite-plugin-pwa";

const hmrClientPort = process.env.HMR_CLIENT_PORT
  ? Number(process.env.HMR_CLIENT_PORT)
  : undefined;

export default defineConfig({
  plugins: [
    vue(),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["favicon.svg", "articles/*.svg"],
      // Android downloads install icons itself; keep them out of the offline bundle.
      includeManifestIcons: false,
      manifest: {
        id: "/",
        name: "Firona — radar du marché malgache",
        short_name: "Firona",
        description: "Ce que les gens cherchent, vendent, et ce qui chauffe sur le marché malgache.",
        theme_color: "#07130e",
        background_color: "#07130e",
        display: "standalone",
        orientation: "portrait",
        start_url: "/now",
        scope: "/",
        lang: "fr",
        categories: ["business", "shopping", "news"],
        icons: [
          { src: "icons/icon-192.png", sizes: "192x192", type: "image/png", purpose: "any" },
          { src: "icons/icon-512.png", sizes: "512x512", type: "image/png", purpose: "any" },
          {
            src: "icons/maskable-512.png",
            sizes: "512x512",
            type: "image/png",
            purpose: "maskable",
          },
          { src: "favicon.svg", sizes: "any", type: "image/svg+xml", purpose: "any" },
        ],
        // Long-press on the Android home-screen icon.
        shortcuts: [
          { name: "Maintenant", short_name: "Maintenant", url: "/now", icons: [{ src: "icons/shortcut-now.png", sizes: "96x96" }] },
          { name: "Futur", short_name: "Futur", url: "/future", icons: [{ src: "icons/shortcut-future.png", sizes: "96x96" }] },
          { name: "Passé", short_name: "Passé", url: "/past", icons: [{ src: "icons/shortcut-past.png", sizes: "96x96" }] },
        ],
      },
      workbox: {
        globPatterns: ["**/*.{js,css,html,svg}", "**/*-latin-wght-normal-*.woff2"],
        globIgnores: ["**/icons/**", "apple-touch-icon.png"],
        navigateFallback: "/index.html",
        navigateFallbackDenylist: [/^\/api\//, /^\/admin\//, /^\/static\//],
        runtimeCaching: [
          {
            // Radar + article JSON: fresh when online, last copy when offline / slow 3G.
            urlPattern: ({ url }) => url.pathname.startsWith("/api/v1/"),
            handler: "NetworkFirst",
            options: {
              cacheName: "firona-api",
              networkTimeoutSeconds: 5,
              expiration: { maxEntries: 120, maxAgeSeconds: 7 * 24 * 3600 },
              cacheableResponse: { statuses: [200] },
            },
          },
        ],
      },
    }),
  ],
  build: {
    target: "es2020",
    cssTarget: "chrome100",
  },
  server: {
    host: true,
    port: 5173,
    allowedHosts: true,
    // When served behind nginx:80, the browser must open the HMR websocket
    // on that public port, not on the internal Vite port 5173.
    hmr: hmrClientPort ? { clientPort: hmrClientPort } : true,
  },
});
