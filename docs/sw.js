self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (e) => e.waitUntil(self.clients.claim()));
self.addEventListener("push", (e) => {
  let d = {}; try { d = e.data ? e.data.json() : {}; } catch { d = { body: e.data && e.data.text() }; }
  e.waitUntil(self.registration.showNotification(d.title || "라밥", { body: d.body || "", icon: "icon-192.png", badge: "icon-192.png", data: { url: d.url || "./" }, tag: "rabap-daily", renotify: true }));
});
self.addEventListener("notificationclick", (e) => {
  e.notification.close(); const url = (e.notification.data && e.notification.data.url) || "./";
  e.waitUntil(self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((cs) => { for (const c of cs) { if (c.url.includes("/rabap/") && "focus" in c) return c.focus(); } return self.clients.openWindow(url); }));
});
