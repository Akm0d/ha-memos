#!/usr/bin/env node
// Fail the Docker build if upstream source layout changes unexpectedly.
import fs from "node:fs";

const root = "/src/web/src";
const prefix = '((window as Window & { __MEMOS_INGRESS_BASE__?: string }).__MEMOS_INGRESS_BASE__ ?? "")';

function replace(path, before, after, count = 1) {
  const file = root + "/" + path;
  const original = fs.readFileSync(file, "utf8");
  const found = original.split(before).length - 1;
  if (found !== count) {
    throw new Error("Ingress source contract changed: " + path + ", expected " + count + ", found " + found);
  }
  fs.writeFileSync(file, original.replaceAll(before, after));
}

replace(
  "router/index.tsx",
  "const router = createBrowserRouter(routeConfig);",
  "const router = createBrowserRouter(routeConfig, { basename: " + prefix + ' || "/" });',
);
replace(
  "connect.ts",
  "baseUrl: window.location.origin,",
  "baseUrl: window.location.origin + " + prefix + ",",
  2,
);
replace(
  "utils/attachment.ts",
  "window.location.origin}/file/",
  "window.location.origin + " + prefix + "}/file/",
  3,
);
replace(
  "hooks/useLiveMemoRefresh.ts",
  'return fetch("/api/sse", {',
  'return fetch(' + prefix + ' + "/api/sse", {',
);
replace(
  "utils/auth-redirect.ts",
  "  const currentPath = window.location.pathname;",
  '  const currentPath = window.location.pathname.slice(' + prefix + '.length) || "/";',
);
replace(
  "utils/auth-redirect.ts",
  "window.location.pathname}",
  "currentPath}",
);
replace(
  "utils/auth-redirect.ts",
  "  window.location.replace(\n    buildAuthRoute({",
  '  window.location.replace(\n    ' + prefix + ' + buildAuthRoute({',
);
console.log("Memos ingress frontend source contract satisfied");
