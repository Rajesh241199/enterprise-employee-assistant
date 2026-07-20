import type {
  ReactNode,
} from "react";
import {
  Navigate,
  useLocation,
} from "react-router-dom";

import {
  getDefaultRoute,
  hasPermission,
  type AppPermission,
} from "../config/accessControl";
import { useAuth } from "../context/AuthContext";


type PermissionRouteProps = {
  permission:
    AppPermission;
  children: ReactNode;
};


export default function PermissionRoute({
  permission,
  children,
}: PermissionRouteProps) {
  const {
    user,
    isAuthenticated,
    isLoading,
  } = useAuth();

  const location =
    useLocation();


  if (isLoading) {
    return (
      <div className="screen-center">
        <div className="loading-card">
          Loading access...
        </div>
      </div>
    );
  }


  if (!isAuthenticated) {
    return (
      <Navigate
        to="/login"
        state={{
          from:
            location.pathname,
        }}
        replace
      />
    );
  }


  if (
    !hasPermission(
      user?.role,
      permission
    )
  ) {
    return (
      <Navigate
        to="/access-denied"
        state={{
          attemptedPath:
            location.pathname,

          returnPath:
            getDefaultRoute(
              user?.role
            ),
        }}
        replace
      />
    );
  }


  return <>{children}</>;
}