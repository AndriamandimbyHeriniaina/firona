/**
 * App-wide singletons: install prompt (Android), connectivity, toasts.
 *
 * @example
 * const { canInstall, install } = useInstallPrompt();
 * const online = useOnline();
 * toast("Radar mis à jour");
 */

import { readonly, ref } from "vue";

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
}

const deferredPrompt = ref<BeforeInstallPromptEvent | null>(null);
const online = ref(typeof navigator === "undefined" ? true : navigator.onLine);

export interface Toast {
  id: number;
  text: string;
  tone: "info" | "error" | "success";
}
const toasts = ref<Toast[]>([]);
let toastId = 0;

if (typeof window !== "undefined") {
  window.addEventListener("beforeinstallprompt", (event) => {
    // Keep Chrome's mini-infobar quiet; we offer our own install button.
    event.preventDefault();
    deferredPrompt.value = event as BeforeInstallPromptEvent;
  });
  window.addEventListener("appinstalled", () => {
    deferredPrompt.value = null;
    toast("Firona est installée sur votre téléphone", "success");
  });
  window.addEventListener("online", () => {
    online.value = true;
  });
  window.addEventListener("offline", () => {
    online.value = false;
  });
}

export function useInstallPrompt() {
  async function install(): Promise<boolean> {
    const event = deferredPrompt.value;
    if (!event) return false;
    deferredPrompt.value = null;
    await event.prompt();
    const choice = await event.userChoice;
    return choice.outcome === "accepted";
  }
  return { canInstall: readonly(deferredPrompt), install };
}

export function useOnline() {
  return readonly(online);
}

export function toast(text: string, tone: Toast["tone"] = "info", ttl = 2800): void {
  const id = ++toastId;
  toasts.value = [...toasts.value.slice(-2), { id, text, tone }];
  window.setTimeout(() => {
    toasts.value = toasts.value.filter((item) => item.id !== id);
  }, ttl);
}

export function useToasts() {
  return readonly(toasts);
}
