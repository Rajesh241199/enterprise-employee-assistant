import {
  ArrowLeft,
  ShieldAlert,
} from "lucide-react";
import {
  Link,
  useLocation,
} from "react-router-dom";

import {
  getDefaultRoute,
} from "../config/accessControl";
import { useAuth } from "../context/AuthContext";


type AccessDeniedState = {
  attemptedPath?: string;
  returnPath?: string;
};


export default function AccessDeniedPage() {
  const {
    user,
  } = useAuth();

  const location =
    useLocation();

  const state =
    location.state as
      AccessDeniedState
      | null;

  const returnPath =
    state?.returnPath ??
    getDefaultRoute(
      user?.role
    );


  return (
    <main className="access-denied-page">
      <section className="access-denied-card">
        <div className="access-denied-icon">
          <ShieldAlert size={34} />
        </div>

        <span>
          Access restricted
        </span>

        <h1>
          You do not have permission
          to open this feature.
        </h1>

        <p>
          Your account is active,
          but your assigned role does
          not include access to this
          page.
        </p>

        {state?.attemptedPath && (
          <code>
            {state.attemptedPath}
          </code>
        )}

        <Link
          to={returnPath}
          replace
        >
          <ArrowLeft size={18} />

          Return to my workspace
        </Link>
      </section>
    </main>
  );
}