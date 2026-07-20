import {
  Briefcase,
  Calculator,
  FileText,
  Lock,
  LogOut,
  MessageSquareText,
  ShieldCheck,
  UserRound,
  Users,
  type LucideIcon,
} from "lucide-react";
import {
  NavLink,
  Outlet,
  useNavigate,
} from "react-router-dom";

import {
  getRoleLabel,
  getVisibleNavigation,
  type NavigationIcon,
} from "../config/accessControl";
import { useAuth } from "../context/AuthContext";


const NAVIGATION_ICONS:
  Record<
    NavigationIcon,
    LucideIcon
  > = {
    chat: MessageSquareText,
    onboarding: Briefcase,
    tax: Calculator,
    employees: Users,
    documents: FileText,
  };


export default function AppLayout() {
  const {
    user,
    logout,
  } = useAuth();

  const navigate = useNavigate();

  const navigationItems =
    getVisibleNavigation(
      user?.role
    );

  const roleLabel =
    getRoleLabel(
      user?.role
    );


  function handleLogout() {
    logout();
    navigate(
      "/login",
      {
        replace: true,
      }
    );
  }


  return (
    <div className="role-app-shell">
      <aside className="role-app-sidebar">
        <div className="role-app-brand">
          <div className="role-app-brand-icon">
            <ShieldCheck size={23} />
          </div>

          <div>
            <strong>
              Internal Employee
              Assistant
            </strong>

            <span>
              Policy Knowledge Portal
            </span>
          </div>
        </div>

        <nav
          className="role-app-navigation"
          aria-label="Application navigation"
        >
          {navigationItems.map(
            (item) => {
              const Icon =
                NAVIGATION_ICONS[
                  item.icon
                ];

              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({
                    isActive,
                  }) =>
                    isActive
                      ? "role-nav-link active"
                      : "role-nav-link"
                  }
                >
                  <Icon size={18} />

                  <span>
                    {item.label}
                  </span>
                </NavLink>
              );
            }
          )}
        </nav>

        <div className="role-app-sidebar-footer">
          <div className="role-access-card">
            <Lock size={18} />

            <div>
              <strong>
                Role access
              </strong>

              <span>
                {roleLabel}
              </span>
            </div>
          </div>

          <div className="role-user-card">
            <div className="role-user-avatar">
              <UserRound size={20} />
            </div>

            <div className="role-user-details">
              <strong>
                {user?.full_name ??
                  "User"}
              </strong>

              <span>
                {user?.email}
              </span>
            </div>
          </div>

          <button
            type="button"
            className="role-logout-button"
            onClick={handleLogout}
          >
            <LogOut size={18} />

            Logout
          </button>
        </div>
      </aside>

      <section className="role-app-content">
        <Outlet />
      </section>
    </div>
  );
}