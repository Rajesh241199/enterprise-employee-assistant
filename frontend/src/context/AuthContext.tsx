import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  getCurrentUser,
  loginUser,
} from "../api/auth";
import {
  TOKEN_STORAGE_KEY,
} from "../api/client";
import type {
  UserProfile,
} from "../types/auth";


type AuthContextValue = {
  user: UserProfile | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  login: (
    email: string,
    password: string
  ) => Promise<UserProfile>;

  logout: () => void;

  refreshUser:
    () => Promise<UserProfile>;
};


const AuthContext =
  createContext<
    AuthContextValue | undefined
  >(undefined);


type AuthProviderProps = {
  children: ReactNode;
};


export function AuthProvider({
  children,
}: AuthProviderProps) {
  const [
    token,
    setToken,
  ] = useState<string | null>(
    () =>
      localStorage.getItem(
        TOKEN_STORAGE_KEY
      )
  );

  const [
    user,
    setUser,
  ] =
    useState<UserProfile | null>(
      null
    );

  const [
    isLoading,
    setIsLoading,
  ] = useState(true);


  async function refreshUser():
    Promise<UserProfile> {
    const profile =
      await getCurrentUser();

    setUser(profile);

    return profile;
  }


  function logout() {
    localStorage.removeItem(
      TOKEN_STORAGE_KEY
    );

    setToken(null);
    setUser(null);
  }


  async function login(
    email: string,
    password: string
  ): Promise<UserProfile> {
    const loginResponse =
      await loginUser({
        email,
        password,
      });

    localStorage.setItem(
      TOKEN_STORAGE_KEY,
      loginResponse.access_token
    );

    setToken(
      loginResponse.access_token
    );

    try {
      const profile =
        await getCurrentUser();

      setUser(profile);

      return profile;

    } catch (error) {
      localStorage.removeItem(
        TOKEN_STORAGE_KEY
      );

      setToken(null);
      setUser(null);

      throw error;
    }
  }


  useEffect(() => {
    let isMounted = true;

    async function loadSession() {
      if (!token) {
        if (isMounted) {
          setUser(null);
          setIsLoading(false);
        }

        return;
      }

      try {
        const profile =
          await getCurrentUser();

        if (isMounted) {
          setUser(profile);
        }

      } catch {
        if (isMounted) {
          localStorage.removeItem(
            TOKEN_STORAGE_KEY
          );

          setToken(null);
          setUser(null);
        }

      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    setIsLoading(true);

    loadSession();

    return () => {
      isMounted = false;
    };
  }, [token]);


  const value =
    useMemo<AuthContextValue>(
      () => ({
        user,
        token,
        isAuthenticated:
          Boolean(
            token && user
          ),
        isLoading,
        login,
        logout,
        refreshUser,
      }),
      [
        user,
        token,
        isLoading,
      ]
    );


  return (
    <AuthContext.Provider
      value={value}
    >
      {children}
    </AuthContext.Provider>
  );
}


export function useAuth() {
  const context =
    useContext(AuthContext);

  if (!context) {
    throw new Error(
      "useAuth must be used "
      + "inside AuthProvider"
    );
  }

  return context;
}