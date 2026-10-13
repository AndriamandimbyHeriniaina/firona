import { createApp } from "vue";
import { createPinia } from "pinia";
import { registerSW } from "virtual:pwa-register";
import "@fontsource-variable/plus-jakarta-sans/wght.css";
import App from "./App.vue";
import { reveal, ripple } from "./directives";
import { isLiteDevice } from "./lib/device";
import { installViewTransitions } from "./lib/viewTransition";
import { router } from "./router";
import "./styles.css";

registerSW({ immediate: true });

if (isLiteDevice()) document.documentElement.classList.add("lite");

installViewTransitions(router);

createApp(App)
  .use(createPinia())
  .use(router)
  .directive("ripple", ripple)
  .directive("reveal", reveal)
  .mount("#app");
