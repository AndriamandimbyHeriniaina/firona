import { createRouter, createWebHistory } from "vue-router";
import RadarView from "./views/RadarView.vue";
import ProductDetailView from "./views/ProductDetailView.vue";

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", redirect: "/now" },
    {
      path: "/now",
      component: RadarView,
      props: { horizon: "now" },
      meta: { title: "Maintenant" },
    },
    {
      path: "/past",
      component: RadarView,
      props: { horizon: "past" },
      meta: { title: "Passé" },
    },
    {
      path: "/future",
      component: RadarView,
      props: { horizon: "future" },
      meta: { title: "Futur" },
    },
    {
      path: "/article/:slug",
      component: ProductDetailView,
      props: true,
      meta: { hideDock: true, compactHeader: true },
    },
  ],
  scrollBehavior() {
    return { top: 0 };
  },
});
