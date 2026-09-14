import "./lib/error-capture";

import { consumeLastCapturedError } from "./lib/error-capture";
import { renderErrorPage } from "./lib/error-page";

type ServerEntry = {
  fetch: (request: Request, env: unknown, ctx: unknown) => Promise<Response> | Response;
};

let serverEntryPromise: Promise<ServerEntry> | undefined;

async function getServerEntry(): Promise<ServerEntry> {
  if (!serverEntryPromise) {
    serverEntryPromise = import("@tanstack/react-start/server-entry").then(
      (m) => (m.default ?? m) as ServerEntry,
    );
  }
  return serverEntryPromise;
}

// h3 swallows in-handler throws into a normal 500 Response with body
// {"unhandled":true,"message":"HTTPError"} — try/catch alone never fires for those.
async function normalizeCatastrophicSsrResponse(response: Response): Promise<Response> {
  if (response.status < 500) return response;
  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes("application/json")) return response;

  const body = await response.clone().text();
  if (!isH3SwallowedErrorBody(body)) return response;

  console.error(consumeLastCapturedError() ?? new Error(`h3 swallowed SSR error: ${body}`));
  return new Response(renderErrorPage(), {
    status: 500,
    headers: { "content-type": "text/html; charset=utf-8" },
  });
}

function isH3SwallowedErrorBody(body: string): boolean {
  try {
    const payload = JSON.parse(body) as { unhandled?: unknown; message?: unknown };
    return payload.unhandled === true && payload.message === "HTTPError";
  } catch {
    return false;
  }
}

const DEFAULT_BACKEND_ORIGIN = "https://decisionflow-api-zess.onrender.com";

export default {
  async fetch(request: Request, env: unknown, ctx: unknown) {
    const url = new URL(request.url);

    // Forward any API requests directly to the Render backend
    if (url.pathname.startsWith("/api/")) {
      const envObj = (env as Record<string, string> | undefined) ?? {};
      const backendBase =
        envObj.BACKEND_URL ||
        envObj.VITE_API_BASE_URL?.replace(/\/api\/.*$/, "") ||
        DEFAULT_BACKEND_ORIGIN;

      const targetUrl = new URL(url.pathname + url.search, backendBase);
      const proxyHeaders = new Headers(request.headers);
      proxyHeaders.set("X-Forwarded-Host", url.host);
      proxyHeaders.set("X-Forwarded-Proto", url.protocol.replace(":", ""));

      const init: RequestInit & { duplex?: string } = {
        method: request.method,
        headers: proxyHeaders,
        redirect: "follow",
      };

      if (request.method !== "GET" && request.method !== "HEAD" && request.body) {
        init.body = request.body;
        init.duplex = "half";
      }

      return await fetch(targetUrl.toString(), init);
    }

    try {
      const handler = await getServerEntry();
      const response = await handler.fetch(request, env, ctx);
      return await normalizeCatastrophicSsrResponse(response);
    } catch (error) {
      console.error(error);
      return new Response(renderErrorPage(), {
        status: 500,
        headers: { "content-type": "text/html; charset=utf-8" },
      });
    }
  },
};
