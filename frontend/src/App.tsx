import type {
  ReactNode,
} from "react";

import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
} from "react-router-dom";

import AppLayout from "./components/AppLayout";
import PermissionRoute from "./components/PermissionRoute";
import {
  getDefaultRoute,
} from "./config/accessControl";
import {
  useAuth,
} from "./context/AuthContext";

import AccessDeniedPage from "./pages/AccessDeniedPage";
import AdminDocumentsPage from "./pages/AdminDocumentsPage";
import AdminOnboardingPage from "./pages/AdminOnboardingPage";
import ChangePasswordPage from "./pages/ChangePasswordPage";
import ChatPage from "./pages/ChatPage";
import LoginPage from "./pages/LoginPage";
import OnboardingPage from "./pages/OnboardingPage";
import TaxCalculatorPage from "./pages/TaxCalculatorPage";


type RouteWrapperProps = {
  children: ReactNode;
};


function LoadingScreen() {
  return (
    <div className="screen-center">
      <div className="loading-card">
        Loading session...
      </div>
    </div>
  );
}


function PublicRoute({
  children,
}: RouteWrapperProps) {
  const {
    user,
    isAuthenticated,
    isLoading,
  } = useAuth();

  if (isLoading) {
    return <LoadingScreen />;
  }

  if (isAuthenticated) {
    const destination =
      user?.must_change_password
        ? "/change-password"
        : getDefaultRoute(
            user?.role
          );

    return (
      <Navigate
        to={destination}
        replace
      />
    );
  }

  return <>{children}</>;
}


function PasswordChangeRoute({
  children,
}: RouteWrapperProps) {
  const {
    user,
    isAuthenticated,
    isLoading,
  } = useAuth();

  if (isLoading) {
    return <LoadingScreen />;
  }

  if (!isAuthenticated) {
    return (
      <Navigate
        to="/login"
        replace
      />
    );
  }

  if (
    !user?.must_change_password
  ) {
    return (
      <Navigate
        to={getDefaultRoute(
          user?.role
        )}
        replace
      />
    );
  }

  return <>{children}</>;
}


function AuthenticatedLayout() {
  const {
    user,
    isAuthenticated,
    isLoading,
  } = useAuth();

  if (isLoading) {
    return <LoadingScreen />;
  }

  if (!isAuthenticated) {
    return (
      <Navigate
        to="/login"
        replace
      />
    );
  }

  if (
    user?.must_change_password
  ) {
    return (
      <Navigate
        to="/change-password"
        replace
      />
    );
  }

  return <AppLayout />;
}


function HomeRedirect() {
  const {
    user,
  } = useAuth();

  return (
    <Navigate
      to={getDefaultRoute(
        user?.role
      )}
      replace
    />
  );
}


export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/login"
          element={
            <PublicRoute>
              <LoginPage />
            </PublicRoute>
          }
        />

        <Route
          path="/change-password"
          element={
            <PasswordChangeRoute>
              <ChangePasswordPage />
            </PasswordChangeRoute>
          }
        />

        <Route
          element={
            <AuthenticatedLayout />
          }
        >
          <Route
            index
            element={
              <HomeRedirect />
            }
          />

          <Route
            path="/chat"
            element={
              <PermissionRoute
                permission="chat:view"
              >
                <ChatPage />
              </PermissionRoute>
            }
          />

          <Route
            path="/onboarding"
            element={
              <PermissionRoute
                permission={
                  "onboarding:self:view"
                }
              >
                <OnboardingPage />
              </PermissionRoute>
            }
          />

          <Route
            path="/tax"
            element={
              <PermissionRoute
                permission="tax:view"
              >
                <TaxCalculatorPage />
              </PermissionRoute>
            }
          />

          <Route
            path="/admin/onboarding"
            element={
              <PermissionRoute
                permission={
                  "employees:manage"
                }
              >
                <AdminOnboardingPage />
              </PermissionRoute>
            }
          />

          <Route
            path="/admin/documents"
            element={
              <PermissionRoute
                permission={
                  "documents:manage"
                }
              >
                <AdminDocumentsPage />
              </PermissionRoute>
            }
          />

          <Route
            path="/access-denied"
            element={
              <AccessDeniedPage />
            }
          />

          <Route
            path="*"
            element={
              <HomeRedirect />
            }
          />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}