import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { api, clearSession, getAccessToken, type ApiRecord } from "./api";

type SessionContextValue = {
  user: ApiRecord | null;
  organization: ApiRecord | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<ApiRecord>;
  signUp: (name: string, email: string, password: string) => Promise<ApiRecord>;
  signOut: () => Promise<void>;
};

const SessionContext = createContext<SessionContextValue | null>(null);

export function SessionProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<ApiRecord | null>(null);
  const [organization, setOrganization] = useState<ApiRecord | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      setLoading(false);
      return;
    }
    api
      .me()
      .then((payload) => {
        setUser(
          payload.user && typeof payload.user === "object" ? (payload.user as ApiRecord) : payload,
        );
        setOrganization(
          payload.organization && typeof payload.organization === "object"
            ? (payload.organization as ApiRecord)
            : null,
        );
      })
      .catch(() => {
        clearSession();
        setUser(null);
        setOrganization(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const value = useMemo<SessionContextValue>(
    () => ({
      user,
      organization,
      loading,
      signIn: async (email, password) => {
        const payload = await api.login({ email, password });
        const next =
          payload.user && typeof payload.user === "object" ? (payload.user as ApiRecord) : payload;
        setUser(next);
        setOrganization(
          payload.organization && typeof payload.organization === "object"
            ? (payload.organization as ApiRecord)
            : null,
        );
        return payload;
      },
      signUp: async (name, email, password) => {
        const cleanName = name.trim() || email.split("@")[0] || "DecisionFlow";
        const orgName = `${cleanName}'s Workspace`;
        const orgSlug =
          `${cleanName}-${email.split("@")[0]}`
            .toLowerCase()
            .replace(/[^a-z0-9]+/g, "-")
            .replace(/^-+|-+$/g, "")
            .slice(0, 48) || "decisionflow-workspace";
        const payload = await api.register({
          org_name: orgName,
          org_slug: orgSlug,
          name: cleanName,
          email: email.trim().toLowerCase(),
          password,
        });
        const hasSession = Boolean(payload.tokens || payload.access_token || payload.user);
        if (hasSession) {
          const next =
            payload.user && typeof payload.user === "object"
              ? (payload.user as ApiRecord)
              : payload;
          setUser(next);
          setOrganization(
            payload.organization && typeof payload.organization === "object"
              ? (payload.organization as ApiRecord)
              : null,
          );
        }
        return payload;
      },
      signOut: async () => {
        await api.logout();
        setUser(null);
        setOrganization(null);
      },
    }),
    [loading, organization, user],
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession() {
  const context = useContext(SessionContext);
  if (!context) throw new Error("useSession must be used inside SessionProvider");
  return context;
}
