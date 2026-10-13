import { createRouter, createWebHistory } from "vue-router";
import type { Horizon } from "./api";
import RadarView from "./views/RadarView.vue";

declare module "vue-router" {
  interface RouteMeta {
    /** Horizon position on screen (0 = Passé, 1 = Maintenant, 2 = Futur). */
    index?: number;
    horizon?: Horizon;
    /** Screens stacked above the radar (article detail). */
    depth?: number;
  }
}

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", redirect: "/now" },
    {
      path: "/past",
      component: RadarView,
      props: { horizon: "past" },
      meta: { index: 0, horizon: "past" },
    },
    {
      path: "/now",
      component: RadarView,
      props: { horizon: "now" },
      meta: { index: 1, horizon: "now" },
    },
    {
      path: "/future",
      component: RadarView,
      props: { horizon: "future" },
      meta: { index: 2, horizon: "future" },
    },
    {
      path: "/article/:slug",
      component: () => import("./views/ProductDetailView.vue"),
      props: true,
      meta: { depth: 1 },
    },
    { path: "/:pathMatch(.*)*", redirect: "/now" },
  ],
  scrollBehavior(_to, _from, savedPosition) {
    return savedPosition ?? { top: 0 };
  },
});
