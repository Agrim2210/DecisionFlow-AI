import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  Outlet,
  Link,
  createRootRouteWithContext,
  useRouter,
  HeadContent,
  Scripts,
} from "@tanstack/react-router";
import { useEffect, type ReactNode } from "react";
import appCss from "../styles.css?url";
import { SessionProvider } from "../lib/session";

function NotFoundComponent() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[#06070c] px-4 text-white">
      <div className="max-w-md text-center">
        <p className="df-kicker">DECISIONFLOW AI</p>
        <h1 className="mt-4 text-7xl font-semibold">404</h1>
        <h2 className="mt-4 text-xl font-semibold">Page not found</h2>
        <p className="mt-2 text-sm text-white/50">
          The flow you are looking for does not exist or has moved.
        </p>
        <Link
          to="/"
          className="mt-6 inline-flex rounded-full bg-white px-5 py-2 text-sm font-semibold text-black"
        >
          Return home
        </Link>
      </div>
    </div>
  );
}

function ErrorComponent({ error, reset }: { error: Error; reset: () => void }) {
  const router = useRouter();
  const errorMessage = error?.message || "An unexpected error occurred while loading this view.";
  return (
    <div className="flex min-h-screen items-center justify-center bg-[#06070c] px-4 text-white">
      <div className="max-w-md text-center">
        <p className="df-kicker">DECISIONFLOW AI</p>
        <h1 className="mt-4 text-2xl font-semibold">Unable to display this view</h1>
        <p className="mt-2 text-sm text-white/50">{errorMessage}</p>
        <div className="mt-6 flex justify-center gap-2">
          <button
            onClick={() => {
              router.invalidate();
              reset();
            }}
            className="rounded-full bg-white px-5 py-2 text-sm font-semibold text-black"
          >
            Retry
          </button>
          <a
            href="/"
            className="rounded-full border border-white/15 px-5 py-2 text-sm text-white/70 hover:text-white"
          >
            Return to landing
          </a>
        </div>
      </div>
    </div>
  );
}

export const Route = createRootRouteWithContext<{ queryClient: QueryClient }>()({
  head: () => ({
    meta: [
      { charSet: "utf-8" },
      { name: "viewport", content: "width=device-width, initial-scale=1" },
      { title: "DecisionFlow AI — Meetings into accountable momentum" },
      {
        name: "description",
        content:
          "Turn meeting transcripts into clear decisions, owned work, and momentum your team can see.",
      },
      { property: "og:title", content: "DecisionFlow AI" },
      {
        property: "og:description",
        content: "Make every meeting leave a trail of decisions and accountable next steps.",
      },
      { property: "og:type", content: "website" },
    ],
    links: [
      { rel: "preconnect", href: "https://fonts.googleapis.com" },
      { rel: "preconnect", href: "https://fonts.gstatic.com", crossOrigin: "anonymous" },
      {
        rel: "stylesheet",
        href: "https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&display=swap",
      },
      { rel: "stylesheet", href: appCss },
      { rel: "icon", href: "/favicon.svg", type: "image/svg+xml" },
      { rel: "icon", href: "/favicon.ico", type: "image/x-icon" },
    ],
  }),
  shellComponent: RootShell,
  component: RootComponent,
  notFoundComponent: NotFoundComponent,
  errorComponent: ErrorComponent,
});

function RootShell({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <head>
        <HeadContent />
      </head>
      <body>
        {children}
        <Scripts />
      </body>
    </html>
  );
}

function RootComponent() {
  const { queryClient } = Route.useRouteContext();
  return (
    <QueryClientProvider client={queryClient}>
      <SessionProvider>
        <Outlet />
      </SessionProvider>
    </QueryClientProvider>
  );
}
