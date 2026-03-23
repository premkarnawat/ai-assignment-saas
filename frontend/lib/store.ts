// frontend/lib/store.ts
import { create } from "zustand";
import { persist } from "zustand/middleware";

interface User {
  id: string;
  email: string;
  name: string;
  avatar_url?: string;
  tier: "free" | "pro" | "team";
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isLoading: boolean;
  setAuth: (user: User, access: string, refresh: string) => void;
  clearAuth: () => void;
  setLoading: (v: boolean) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isLoading: false,
      setAuth: (user, accessToken, refreshToken) => {
        // Also set in localStorage for axios interceptor
        localStorage.setItem("access_token", accessToken);
        localStorage.setItem("refresh_token", refreshToken);
        set({ user, accessToken, refreshToken });
      },
      clearAuth: () => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        set({ user: null, accessToken: null, refreshToken: null });
      },
      setLoading: (isLoading) => set({ isLoading }),
    }),
    { name: "auth-store", partialize: (s) => ({ user: s.user }) }
  )
);
