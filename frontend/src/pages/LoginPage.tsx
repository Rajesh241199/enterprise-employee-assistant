import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Lock, Server, ShieldCheck, UserRound } from "lucide-react";
import { apiClient, getApiErrorMessage } from "../api/client";
import { useAuth } from "../context/AuthContext";

const demoUsers = [
  {
    label: "Employee",
    email: "rajesh.employee@company.com",
    password: "Password@123",
    description: "Access to all-employee policies",
  },
  {
    label: "HR Admin",
    email: "priya.hr@company.com",
    password: "Password@123",
    description: "Access to HR-only policies",
  },
  {
    label: "Finance Admin",
    email: "meera.finance@company.com",
    password: "Password@123",
    description: "Access to finance-only policies",
  },
  {
    label: "IT Admin",
    email: "karthik.it@company.com",
    password: "Password@123",
    description: "Access to IT-only policies",
  },
];

export default function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [email, setEmail] = useState("rajesh.employee@company.com");
  const [password, setPassword] = useState("Password@123");
  const [backendStatus, setBackendStatus] = useState("Checking backend...");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    async function checkBackend() {
      try {
        const response = await apiClient.get("/ready");
        const services = response.data?.services;

        setBackendStatus(
          `Backend ready · Postgres: ${services?.postgres ?? "ok"} · Qdrant: ${
            services?.qdrant ?? "ok"
          }`
        );
      } catch {
        setBackendStatus("Backend is not reachable. Start FastAPI first.");
      }
    }

    checkBackend();
  }, []);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setError("");
    setIsSubmitting(true);

    try {
      await login(email, password);
      navigate("/chat");
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  function selectDemoUser(user: (typeof demoUsers)[number]) {
    setEmail(user.email);
    setPassword(user.password);
    setError("");
  }

  return (
    <main className="login-shell">
      <section className="login-left">
        <div className="brand-badge">
          <ShieldCheck size={22} />
          Internal Assistant
        </div>

        <h1>Internal Employee Assistant</h1>

        <p className="hero-text">
          Secure internal policy assistant with role-based access control,
          document-grounded answers, source citations, audit logging, and
          security guardrails.
        </p>

        <div className="feature-grid">
          <div className="feature-card">
            <ShieldCheck size={20} />
            <span>RBAC protected</span>
          </div>
          <div className="feature-card">
            <Server size={20} />
            <span>Backend connected</span>
          </div>
          <div className="feature-card">
            <Lock size={20} />
            <span>JWT authentication</span>
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
            <p>Use one of the seeded test users.</p>
          </div>
        </div>

        <div className="backend-status">{backendStatus}</div>

        <form onSubmit={handleSubmit} className="form-stack">
          <label>
            Email
            <input
              type="email"
              value={email}
              autoComplete="email"
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </label>

          <label>
            Password
            <input
              type="password"
              value={password}
              autoComplete="current-password"
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </label>

          {error && <div className="error-box">{error}</div>}

          <button type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Signing in..." : "Sign in"}
          </button>
        </form>

        <div className="demo-section">
          <p>Demo accounts</p>

          <div className="demo-grid">
            {demoUsers.map((user) => (
              <button
                key={user.email}
                type="button"
                className="demo-user-button"
                onClick={() => selectDemoUser(user)}
              >
                <strong>{user.label}</strong>
                <span>{user.description}</span>
              </button>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}