import { createRouter, createWebHistory } from "vue-router";
import RadarView from "./views/RadarView.vue";

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", redirect: "/now" },
    { path: "/now", component: RadarView, props: { horizon: "now" } },
    { path: "/past", component: RadarView, props: { horizon: "past" } },
    { path: "/future", component: RadarView, props: { horizon: "future" } },
  ],
});
