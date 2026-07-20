import {
  AlertTriangle,
  Briefcase,
  Building2,
  Calculator,
  CalendarDays,
  CheckCircle2,
  FileText,
  Lock,
  LogOut,
  Mail,
  MapPin,
  MessageSquareText,
  RefreshCw,
  ShieldCheck,
  UserRound,
  Users,
} from "lucide-react";
import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { Link } from "react-router-dom";

import { getApiErrorMessage } from "../api/client";
import { getMyOnboardingProfile } from "../api/onboarding";
import { useAuth } from "../context/AuthContext";
import type {
  OnboardingContact,
  OnboardingProfileResponse,
} from "../types/onboarding";


type DetailRowProps = {
  label: string;
  value: ReactNode;
};


function getRoleLabel(role: string): string {
  const labels: Record<string, string> = {
    employee: "Employee",
    hr_admin: "HR Admin",
    finance_admin: "Finance Admin",
    it_admin: "IT Admin",
    super_admin: "Super Admin",
  };

  return labels[role] ?? role;
}


function isAdminRole(role?: string): boolean {
  return [
    "hr_admin",
    "finance_admin",
    "it_admin",
    "super_admin",
  ].includes(role ?? "");
}


function valueOrPending(
  value: string | null | undefined
): string {
  const normalizedValue = value?.trim();

  return normalizedValue || "Not assigned yet";
}


function formatDate(
  value: string | null | undefined
): string {
  if (!value) {
    return "Not assigned yet";
  }

  const parsedDate = new Date(`${value}T00:00:00`);

  if (Number.isNaN(parsedDate.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en-IN", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  }).format(parsedDate);
}


function formatStatus(status: string): string {
  return status
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) =>
      character.toUpperCase()
    );
}


function DetailRow({
  label,
  value,
}: DetailRowProps) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}


function EmailValue({
  email,
}: {
  email: string | null | undefined;
}) {
  if (!email) {
    return (
      <span className="pending-value">
        Not assigned yet
      </span>
    );
  }

  return (
    <a
      className="onboarding-email-link"
      href={`mailto:${email}`}
    >
      <Mail size={15} />
      {email}
    </a>
  );
}


function ContactCard({
  title,
  contact,
  icon,
}: {
  title: string;
  contact: OnboardingContact;
  icon: ReactNode;
}) {
  return (
    <article className="onboarding-contact-card">
      <div className="onboarding-contact-icon">
        {icon}
      </div>

      <div>
        <span className="onboarding-contact-label">
          {title}
        </span>

        <strong>
          {valueOrPending(contact.name)}
        </strong>

        <EmailValue email={contact.email} />
      </div>
    </article>
  );
}


export default function OnboardingPage() {
  const { user, logout } = useAuth();

  const [profile, setProfile] =
    useState<OnboardingProfileResponse | null>(
      null
    );

  const [isLoading, setIsLoading] =
    useState(true);

  const [isRefreshing, setIsRefreshing] =
    useState(false);

  const [error, setError] =
    useState<string | null>(null);

  const roleLabel = useMemo(
    () => getRoleLabel(user?.role ?? ""),
    [user?.role]
  );


  const loadProfile = useCallback(
    async (refresh = false) => {
      if (refresh) {
        setIsRefreshing(true);
      } else {
        setIsLoading(true);
      }

      setError(null);

      try {
        const profileResponse =
          await getMyOnboardingProfile();

        setProfile(profileResponse);
      } catch (requestError) {
        setError(
          getApiErrorMessage(requestError)
        );
      } finally {
        setIsLoading(false);
        setIsRefreshing(false);
      }
    },
    []
  );


  useEffect(() => {
    loadProfile();
  }, [loadProfile]);


  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <ShieldCheck size={24} />

          <div>
            <strong>
              Internal Employee Assistant
            </strong>

            <span>
              Policy Knowledge Portal
            </span>
          </div>
        </div>

        <nav className="sidebar-nav">
          <Link to="/chat">
            <MessageSquareText size={18} />
            Chat
          </Link>

          <Link
            className="active"
            to="/onboarding"
          >
            <Briefcase size={18} />
            My Onboarding
          </Link>

          <Link to="/tax">
            <Calculator size={18} />
            Tax Calculator
          </Link>

          {isAdminRole(user?.role) && (
            <Link to="/admin/documents">
              <FileText size={18} />
              Documents
            </Link>
          )}
        </nav>

        <div className="access-card">
          <Lock size={18} />

          <div>
            <strong>Role access</strong>
            <span>{roleLabel}</span>
          </div>
        </div>

        <div className="user-card">
          <div className="avatar">
            <UserRound size={20} />
          </div>

          <div>
            <strong>
              {user?.full_name ?? "User"}
            </strong>

            <span>{user?.email}</span>
          </div>
        </div>
      </aside>

      <section className="main-panel onboarding-panel">
        <header className="topbar">
          <div>
            <h1>My Onboarding</h1>

            <p>
              View your department, business
              unit, manager, project assignment
              and onboarding contacts.
            </p>
          </div>

          <div className="onboarding-topbar-actions">
            <button
              type="button"
              className="secondary-button"
              onClick={() => loadProfile(true)}
              disabled={isRefreshing}
            >
              <RefreshCw
                size={18}
                className={
                  isRefreshing
                    ? "spinning-icon"
                    : ""
                }
              />

              {isRefreshing
                ? "Refreshing..."
                : "Refresh"}
            </button>

            <button
              type="button"
              className="secondary-button"
              onClick={logout}
            >
              <LogOut size={18} />
              Logout
            </button>
          </div>
        </header>

        {isLoading && (
          <div className="onboarding-loading-card">
            <RefreshCw
              size={22}
              className="spinning-icon"
            />

            <span>
              Loading your onboarding details...
            </span>
          </div>
        )}

        {error && !isLoading && (
          <div
            className="onboarding-alert error"
            role="alert"
          >
            <AlertTriangle size={20} />

            <div>
              <strong>
                Could not load onboarding details
              </strong>

              <span>{error}</span>
            </div>

            <button
              type="button"
              onClick={() => loadProfile()}
            >
              Try again
            </button>
          </div>
        )}

        {profile && !isLoading && (
          <>
            <section
              className={`onboarding-status-banner ${
                profile.profile_complete
                  ? "complete"
                  : "pending"
              }`}
            >
              <div className="onboarding-status-icon">
                {profile.profile_complete ? (
                  <CheckCircle2 size={24} />
                ) : (
                  <AlertTriangle size={24} />
                )}
              </div>

              <div>
                <strong>
                  {profile.profile_complete
                    ? "Your onboarding profile is complete"
                    : "Some onboarding details are pending"}
                </strong>

                <span>
                  Status:{" "}
                  {formatStatus(
                    profile.onboarding_status
                  )}
                </span>
              </div>
            </section>

            <div className="onboarding-grid">
              <article className="onboarding-card">
                <div className="onboarding-card-header">
                  <div className="onboarding-section-icon">
                    <UserRound size={21} />
                  </div>

                  <div>
                    <span>Employee profile</span>
                    <h2>
                      Personal and organizational
                      details
                    </h2>
                  </div>
                </div>

                <dl className="onboarding-details">
                  <DetailRow
                    label="Employee name"
                    value={
                      profile.employee.full_name
                    }
                  />

                  <DetailRow
                    label="Employee ID"
                    value={
                      profile.employee.employee_id
                    }
                  />

                  <DetailRow
                    label="Email address"
                    value={
                      <EmailValue
                        email={
                          profile.employee.email
                        }
                      />
                    }
                  />

                  <DetailRow
                    label="Designation"
                    value={valueOrPending(
                      profile.employee.designation
                    )}
                  />

                  <DetailRow
                    label="Location"
                    value={
                      <span className="onboarding-detail-with-icon">
                        <MapPin size={15} />

                        {valueOrPending(
                          profile.employee.location
                        )}
                      </span>
                    }
                  />

                  <DetailRow
                    label="Department"
                    value={valueOrPending(
                      profile.employee.department
                    )}
                  />

                  <DetailRow
                    label="Business unit"
                    value={valueOrPending(
                      profile.employee.business_unit
                    )}
                  />
                </dl>
              </article>

              <article className="onboarding-card">
                <div className="onboarding-card-header">
                  <div className="onboarding-section-icon">
                    <Users size={21} />
                  </div>

                  <div>
                    <span>
                      Reporting structure
                    </span>

                    <h2>
                      Your reporting manager
                    </h2>
                  </div>
                </div>

                <dl className="onboarding-details">
                  <DetailRow
                    label="Manager name"
                    value={valueOrPending(
                      profile.manager.name
                    )}
                  />

                  <DetailRow
                    label="Manager email"
                    value={
                      <EmailValue
                        email={
                          profile.manager.email
                        }
                      />
                    }
                  />

                  <DetailRow
                    label="Department"
                    value={valueOrPending(
                      profile.employee.department
                    )}
                  />

                  <DetailRow
                    label="Business unit"
                    value={valueOrPending(
                      profile.employee.business_unit
                    )}
                  />
                </dl>
              </article>

              <article className="onboarding-card">
                <div className="onboarding-card-header">
                  <div className="onboarding-section-icon">
                    <Briefcase size={21} />
                  </div>

                  <div>
                    <span>
                      Project assignment
                    </span>

                    <h2>
                      Your assigned project
                    </h2>
                  </div>
                </div>

                <dl className="onboarding-details">
                  <DetailRow
                    label="Project name"
                    value={valueOrPending(
                      profile.project.name
                    )}
                  />

                  <DetailRow
                    label="Project role"
                    value={valueOrPending(
                      profile.project.role
                    )}
                  />

                  <DetailRow
                    label="Project start date"
                    value={
                      <span className="onboarding-detail-with-icon">
                        <CalendarDays size={15} />

                        {formatDate(
                          profile.project.start_date
                        )}
                      </span>
                    }
                  />

                  <DetailRow
                    label="Assignment status"
                    value={formatStatus(
                      profile.onboarding_status
                    )}
                  />
                </dl>
              </article>

              <article className="onboarding-card">
                <div className="onboarding-card-header">
                  <div className="onboarding-section-icon">
                    <Building2 size={21} />
                  </div>

                  <div>
                    <span>
                      Organization placement
                    </span>

                    <h2>
                      Where you will be working
                    </h2>
                  </div>
                </div>

                <dl className="onboarding-details">
                  <DetailRow
                    label="Business unit"
                    value={valueOrPending(
                      profile.employee.business_unit
                    )}
                  />

                  <DetailRow
                    label="Department"
                    value={valueOrPending(
                      profile.employee.department
                    )}
                  />

                  <DetailRow
                    label="Project"
                    value={valueOrPending(
                      profile.project.name
                    )}
                  />

                  <DetailRow
                    label="Project role"
                    value={valueOrPending(
                      profile.project.role
                    )}
                  />
                </dl>
              </article>
            </div>

            <section className="onboarding-contacts-section">
              <div className="onboarding-contacts-heading">
                <div>
                  <span>
                    People who can support you
                  </span>

                  <h2>
                    Your onboarding contacts
                  </h2>
                </div>

                <ShieldCheck size={24} />
              </div>

              <div className="onboarding-contact-grid">
                <ContactCard
                  title="HR POC"
                  contact={profile.poc.hr_poc}
                  icon={<Users size={20} />}
                />

                <ContactCard
                  title="IT POC"
                  contact={profile.poc.it_poc}
                  icon={<ShieldCheck size={20} />}
                />

                <ContactCard
                  title="Onboarding buddy"
                  contact={profile.poc.buddy}
                  icon={<UserRound size={20} />}
                />
              </div>
            </section>
          </>
        )}
      </section>
    </main>
  );
}