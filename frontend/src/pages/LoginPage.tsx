import {
  useEffect,
  useState,
  type FormEvent,
} from "react";
import {
  useNavigate,
} from "react-router-dom";
import {
  Lock,
  Server,
  ShieldCheck,
  UserRound,
} from "lucide-react";

import {
  apiClient,
  getApiErrorMessage,
} from "../api/client";
import {
  getDefaultRoute,
} from "../config/accessControl";
import {
  useAuth,
} from "../context/AuthContext";


export default function LoginPage() {
  const navigate =
    useNavigate();

  const {
    login,
  } = useAuth();

  const [
    email,
    setEmail,
  ] = useState("");

  const [
    password,
    setPassword,
  ] = useState("");

  const [
    backendStatus,
    setBackendStatus,
  ] = useState(
    "Checking backend..."
  );

  const [
    error,
    setError,
  ] = useState("");

  const [
    isSubmitting,
    setIsSubmitting,
  ] = useState(false);


  useEffect(() => {
    async function checkBackend() {
      try {
        const response =
          await apiClient.get(
            "/ready"
          );

        const services =
          response.data?.services;

        setBackendStatus(
          "Backend ready"
          + " · Postgres: "
          + (
            services?.postgres
            ?? "ok"
          )
          + " · Qdrant: "
          + (
            services?.qdrant
            ?? "ok"
          )
        );

      } catch {
        setBackendStatus(
          "Backend is not reachable."
        );
      }
    }

    checkBackend();
  }, []);


  async function handleSubmit(
    event:
      FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    setError("");
    setIsSubmitting(true);

    try {
      const profile =
        await login(
          email,
          password
        );

      const destination =
        profile.must_change_password
          ? "/change-password"
          : getDefaultRoute(
              profile.role
            );

      navigate(
        destination,
        {
          replace: true,
        }
      );

    } catch (requestError) {
      setError(
        getApiErrorMessage(
          requestError
        )
      );

    } finally {
      setIsSubmitting(false);
    }
  }


  return (
    <main className="login-shell">
      <section className="login-left">
        <div className="brand-badge">
          <ShieldCheck size={22} />

          Internal Assistant
        </div>

        <h1>
          Internal Employee Assistant
        </h1>

        <p className="hero-text">
          Secure internal policy
          assistant with role-based
          access control,
          document-grounded answers,
          source citations, audit
          logging and security
          guardrails.
        </p>

        <div className="feature-grid">
          <div className="feature-card">
            <ShieldCheck size={20} />

            <span>
              RBAC protected
            </span>
          </div>

          <div className="feature-card">
            <Server size={20} />

            <span>
              Backend connected
            </span>
          </div>

          <div className="feature-card">
            <Lock size={20} />

            <span>
              JWT authentication
            </span>
          </div>
        </div>
      </section>

      <section className="login-card">
        <div className="card-header">
          <div className="icon-circle">
            <UserRound size={24} />
          </div>

          <div>
            <h2>Sign in</h2>

            <p>
              Enter your company
              credentials.
            </p>
          </div>
        </div>

        <div className="backend-status">
          {backendStatus}
        </div>

        <form
          onSubmit={handleSubmit}
          className="form-stack"
        >
          <label>
            Company email

            <input
              type="email"
              value={email}
              autoComplete="email"
              placeholder={
                "name@company.com"
              }
              onChange={(event) =>
                setEmail(
                  event.target.value
                )
              }
              required
            />
          </label>

          <label>
            Password

            <input
              type="password"
              value={password}
              autoComplete={
                "current-password"
              }
              onChange={(event) =>
                setPassword(
                  event.target.value
                )
              }
              required
            />
          </label>

          {error && (
            <div className="error-box">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
          >
            {isSubmitting
              ? "Signing in..."
              : "Sign in"}
          </button>
        </form>

        <p className="login-security-note">
          New employees must replace
          their temporary password
          before accessing company
          features.
        </p>
      </section>
    </main>
  );
}