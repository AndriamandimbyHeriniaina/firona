import type { Directive } from "vue";
import { prefersReducedMotion } from "../lib/device";

/**
 * Material-style touch ripple (transform + opacity only, GPU friendly).
 *
 * @example
 * <button v-ripple>…</button>
 */
export const ripple: Directive<HTMLElement> = {
  mounted(el) {
    el.classList.add("has-ripple");
    el.addEventListener(
      "pointerdown",
      (event: PointerEvent) => {
        if (prefersReducedMotion() || event.button !== 0) return;
        const rect = el.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height) * 2.2;
        const ink = document.createElement("span");
        ink.className = "ripple-ink";
        ink.style.width = ink.style.height = `${size}px`;
        ink.style.left = `${event.clientX - rect.left - size / 2}px`;
        ink.style.top = `${event.clientY - rect.top - size / 2}px`;
        el.appendChild(ink);
        const remove = () => ink.remove();
        ink.addEventListener("animationend", remove, { once: true });
        window.setTimeout(remove, 900);
      },
      { passive: true },
    );
  },
};

/**
 * Adds `.is-in` once the element scrolls into view (bars, rings, charts).
 *
 * @example
 * <div v-reveal class="bar">…</div>
 */
export const reveal: Directive<HTMLElement> = {
  mounted(el) {
    if (!("IntersectionObserver" in window)) {
      el.classList.add("is-in");
      return;
    }
    const observer = new IntersectionObserver(
      (entries) => {
        for (const item of entries) {
          if (item.isIntersecting) {
            el.classList.add("is-in");
            observer.disconnect();
          }
        }
      },
      { rootMargin: "0px 0px -8% 0px" },
    );
    observer.observe(el);
    (el as HTMLElement & { _reveal?: IntersectionObserver })._reveal = observer;
  },
  unmounted(el) {
    (el as HTMLElement & { _reveal?: IntersectionObserver })._reveal?.disconnect();
  },
};

declare module "vue" {
  interface GlobalDirectives {
    vRipple: typeof ripple;
    vReveal: typeof reveal;
  }
}
