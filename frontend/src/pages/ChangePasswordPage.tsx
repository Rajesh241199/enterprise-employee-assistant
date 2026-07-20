import {
  CheckCircle2,
  Eye,
  EyeOff,
  KeyRound,
  LockKeyhole,
  LogOut,
  ShieldCheck,
} from "lucide-react";
import {
  useMemo,
  useState,
  type FormEvent,
} from "react";
import {
  useNavigate,
} from "react-router-dom";

import {
  changePassword,
} from "../api/auth";
import {
  getApiErrorMessage,
} from "../api/client";
import {
  getDefaultRoute,
} from "../config/accessControl";
import {
  useAuth,
} from "../context/AuthContext";


function hasUppercase(
  value: string
): boolean {
  return /[A-Z]/.test(value);
}


function hasLowercase(
  value: string
): boolean {
  return /[a-z]/.test(value);
}


function hasNumber(
  value: string
): boolean {
  return /\d/.test(value);
}


function hasSpecialCharacter(
  value: string
): boolean {
  return /[^A-Za-z0-9]/.test(
    value
  );
}


export default function ChangePasswordPage() {
  const navigate =
    useNavigate();

  const {
    user,
    logout,
    refreshUser,
  } = useAuth();

  const [
    currentPassword,
    setCurrentPassword,
  ] = useState("");

  const [
    newPassword,
    setNewPassword,
  ] = useState("");

  const [
    confirmPassword,
    setConfirmPassword,
  ] = useState("");

  const [
    showPasswords,
    setShowPasswords,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState("");

  const [
    isSubmitting,
    setIsSubmitting,
  ] = useState(false);


  const requirements =
    useMemo(
      () => [
        {
          label:
            "At least 12 characters",
          passed:
            newPassword.length >= 12,
        },
        {
          label:
            "One uppercase letter",
          passed:
            hasUppercase(
              newPassword
            ),
        },
        {
          label:
            "One lowercase letter",
          passed:
            hasLowercase(
              newPassword
            ),
        },
        {
          label:
            "One number",
          passed:
            hasNumber(
              newPassword
            ),
        },
        {
          label:
            "One special character",
          passed:
            hasSpecialCharacter(
              newPassword
            ),
        },
      ],
      [newPassword]
    );


  const passwordIsValid =
    requirements.every(
      (requirement) =>
        requirement.passed
    );


  async function handleSubmit(
    event:
      FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    setError("");

    if (!passwordIsValid) {
      setError(
        "The new password does not "
        + "meet all security "
        + "requirements."
      );

      return;
    }

    if (
      newPassword
      !== confirmPassword
    ) {
      setError(
        "New password and "
        + "confirmation password "
        + "do not match."
      );

      return;
    }

    if (
      currentPassword
      === newPassword
    ) {
      setError(
        "New password must be "
        + "different from the "
        + "temporary password."
      );

      return;
    }

    setIsSubmitting(true);

    try {
      await changePassword({
        current_password:
          currentPassword,

        new_password:
          newPassword,

        confirm_password:
          confirmPassword,
      });

      const profile =
        await refreshUser();

      navigate(
        getDefaultRoute(
          profile.role
        ),
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
    <main className="password-change-page">
      <section className="password-change-card">
        <div className="password-change-brand">
          <ShieldCheck size={22} />

          Internal Employee Assistant
        </div>

        <div className="password-change-icon">
          <LockKeyhole size={32} />
        </div>

        <span className="password-change-label">
          Security action required
        </span>

        <h1>
          Create your permanent
          password
        </h1>

        <p>
          Hello{" "}
          <strong>
            {user?.full_name
              ?? "Employee"}
          </strong>
          . Your current password is
          temporary. Change it before
          accessing the application.
        </p>

        <form
          className="password-change-form"
          onSubmit={handleSubmit}
        >
          <label>
            Temporary password

            <div className="password-input-wrapper">
              <KeyRound size={18} />

              <input
                type={
                  showPasswords
                    ? "text"
                    : "password"
                }
                value={currentPassword}
                autoComplete={
                  "current-password"
                }
                onChange={(event) =>
                  setCurrentPassword(
                    event.target.value
                  )
                }
                required
              />
            </div>
          </label>

          <label>
            New password

            <div className="password-input-wrapper">
              <LockKeyhole size={18} />

              <input
                type={
                  showPasswords
                    ? "text"
                    : "password"
                }
                value={newPassword}
                autoComplete={
                  "new-password"
                }
                onChange={(event) =>
                  setNewPassword(
                    event.target.value
                  )
                }
                required
              />
            </div>
          </label>

          <label>
            Confirm new password

            <div className="password-input-wrapper">
              <LockKeyhole size={18} />

              <input
                type={
                  showPasswords
                    ? "text"
                    : "password"
                }
                value={confirmPassword}
                autoComplete={
                  "new-password"
                }
                onChange={(event) =>
                  setConfirmPassword(
                    event.target.value
                  )
                }
                required
              />
            </div>
          </label>

          <button
            type="button"
            className="password-visibility-button"
            onClick={() =>
              setShowPasswords(
                (current) =>
                  !current
              )
            }
          >
            {showPasswords ? (
              <EyeOff size={17} />
            ) : (
              <Eye size={17} />
            )}

            {showPasswords
              ? "Hide passwords"
              : "Show passwords"}
          </button>

          <div className="password-requirements">
            <strong>
              Password requirements
            </strong>

            {requirements.map(
              (requirement) => (
                <div
                  key={
                    requirement.label
                  }
                  className={
                    requirement.passed
                      ? "passed"
                      : ""
                  }
                >
                  <CheckCircle2
                    size={16}
                  />

                  <span>
                    {
                      requirement.label
                    }
                  </span>
                </div>
              )
            )}
          </div>

          {error && (
            <div
              className="error-box"
              role="alert"
            >
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
          >
            {isSubmitting
              ? "Changing password..."
              : "Change password and continue"}
          </button>
        </form>

        <button
          type="button"
          className="password-change-logout"
          onClick={logout}
        >
          <LogOut size={17} />

          Sign out
        </button>
      </section>
    </main>
  );
}