import {
  AlertTriangle,
  Briefcase,
  Calculator,
  CheckCircle2,
  Eye,
  FileText,
  Lock,
  LogOut,
  MessageSquareText,
  Pencil,
  Plus,
  RefreshCw,
  Save,
  ShieldCheck,
  UserPlus,
  UserRound,
  Users,
  X,
} from "lucide-react";
import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type FormEvent,
} from "react";
import {
  Link,
  Navigate,
} from "react-router-dom";

import {
  createEmployeeOnboardingRecord,
  listEmployeeOnboardingRecords,
  updateEmployeeOnboardingRecord,
} from "../api/adminOnboarding";
import { getApiErrorMessage } from "../api/client";
import { useAuth } from "../context/AuthContext";
import type {
  CreateEmployeeOnboardingRequest,
  EmployeeOnboardingRecord,
  UpdateEmployeeOnboardingRequest,
} from "../types/adminOnboarding";


type EmployeeFormState = {
  employeeId: string;
  fullName: string;
  email: string;
  temporaryPassword: string;

  designation: string;
  location: string;
  department: string;
  businessUnit: string;

  managerName: string;
  managerEmail: string;

  projectName: string;
  projectRole: string;
  projectStartDate: string;

  onboardingStatus: string;
  isActive: boolean;

  hrPocName: string;
  hrPocEmail: string;

  itPocName: string;
  itPocEmail: string;

  buddyName: string;
  buddyEmail: string;
};


const INITIAL_FORM: EmployeeFormState = {
  employeeId: "",
  fullName: "",
  email: "",
  temporaryPassword: "Welcome@1234",

  designation: "",
  location: "Bengaluru",
  department: "Data Science",
  businessUnit: "Digital & AI",

  managerName: "",
  managerEmail: "",

  projectName: "",
  projectRole: "",
  projectStartDate: "",

  onboardingStatus: "assigned",
  isActive: true,

  hrPocName: "",
  hrPocEmail: "",

  itPocName: "",
  itPocEmail: "",

  buddyName: "",
  buddyEmail: "",
};


function canManageOnboarding(
  role?: string
): boolean {
  return [
    "hr_admin",
    "super_admin",
  ].includes(role ?? "");
}


function isDocumentAdmin(
  role?: string
): boolean {
  return [
    "hr_admin",
    "finance_admin",
    "it_admin",
    "super_admin",
  ].includes(role ?? "");
}


function getRoleLabel(
  role: string
): string {
  const labels: Record<string, string> = {
    employee: "Employee",
    hr_admin: "HR Admin",
    finance_admin: "Finance Admin",
    it_admin: "IT Admin",
    super_admin: "Super Admin",
  };

  return labels[role] ?? role;
}


function optionalValue(
  value: string
): string | null {
  const normalized = value.trim();

  return normalized || null;
}


function formatDate(
  value: string | null
): string {
  if (!value) {
    return "Not assigned";
  }

  const parsedDate = new Date(
    `${value}T00:00:00`
  );

  if (
    Number.isNaN(
      parsedDate.getTime()
    )
  ) {
    return value;
  }

  return new Intl.DateTimeFormat(
    "en-IN",
    {
      day: "2-digit",
      month: "short",
      year: "numeric",
    }
  ).format(parsedDate);
}


function formatStatus(
  value: string
): string {
  return value
    .replaceAll("_", " ")
    .replace(
      /\b\w/g,
      (character) =>
        character.toUpperCase()
    );
}


function buildCreatePayload(
  form: EmployeeFormState
): CreateEmployeeOnboardingRequest {
  return {
    employee_id:
      form.employeeId.trim(),

    full_name:
      form.fullName.trim(),

    email:
      form.email.trim().toLowerCase(),

    temporary_password:
      form.temporaryPassword,

    designation:
      optionalValue(
        form.designation
      ),

    location:
      form.location.trim(),

    department:
      form.department.trim(),

    business_unit:
      optionalValue(
        form.businessUnit
      ),

    manager_name:
      optionalValue(
        form.managerName
      ),

    manager_email:
      optionalValue(
        form.managerEmail
      ),

    project_name:
      optionalValue(
        form.projectName
      ),

    project_role:
      optionalValue(
        form.projectRole
      ),

    project_start_date:
      optionalValue(
        form.projectStartDate
      ),

    onboarding_status:
      form.onboardingStatus,

    is_active:
      form.isActive,

    hr_poc_name:
      optionalValue(
        form.hrPocName
      ),

    hr_poc_email:
      optionalValue(
        form.hrPocEmail
      ),

    it_poc_name:
      optionalValue(
        form.itPocName
      ),

    it_poc_email:
      optionalValue(
        form.itPocEmail
      ),

    buddy_name:
      optionalValue(
        form.buddyName
      ),

    buddy_email:
      optionalValue(
        form.buddyEmail
      ),
  };
}


function validateCreateForm(
  form: EmployeeFormState
): string | null {
  if (!form.employeeId.trim()) {
    return "Employee ID is required.";
  }

  if (!form.fullName.trim()) {
    return "Employee name is required.";
  }

  if (!form.email.trim()) {
    return "Employee email is required.";
  }

  if (
    form.temporaryPassword.length < 12
  ) {
    return (
      "Temporary password must contain " +
      "at least 12 characters."
    );
  }

  if (!form.location.trim()) {
    return "Location is required.";
  }

  if (!form.department.trim()) {
    return "Department is required.";
  }

  if (
    form.managerName.trim() &&
    !form.managerEmail.trim()
  ) {
    return (
      "Manager email is required when " +
      "manager name is provided."
    );
  }

  if (
    form.managerEmail.trim() &&
    !form.managerName.trim()
  ) {
    return (
      "Manager name is required when " +
      "manager email is provided."
    );
  }

  if (
    form.projectStartDate &&
    !form.projectName.trim()
  ) {
    return (
      "Project name is required when " +
      "a project start date is provided."
    );
  }

  return null;
}


function EmployeeSummaryCard({
  record,
  onView,
  onEditBuddy,
  onToggleStatus,
}: {
  record: EmployeeOnboardingRecord;
  onView:
    (record: EmployeeOnboardingRecord) => void;
  onEditBuddy:
    (record: EmployeeOnboardingRecord) => void;
  onToggleStatus:
    (record: EmployeeOnboardingRecord) => void;
}) {
  return (
    <article className="employee-admin-card">
      <div className="employee-admin-card-header">
        <div className="avatar">
          <UserRound size={20} />
        </div>

        <div>
          <strong>
            {record.employee.full_name}
          </strong>

          <span>
            {record.employee.employee_id}
          </span>
        </div>

        <span
          className={`employee-status-pill ${
            record.is_active
              ? "active"
              : "inactive"
          }`}
        >
          {record.is_active
            ? "Active"
            : "Inactive"}
        </span>
      </div>

      <dl className="employee-admin-summary">
        <div>
          <dt>Department</dt>

          <dd>
            {record.employee.department ??
              "Not assigned"}
          </dd>
        </div>

        <div>
          <dt>Business unit</dt>

          <dd>
            {record.employee.business_unit ??
              "Not assigned"}
          </dd>
        </div>

        <div>
          <dt>Manager</dt>

          <dd>
            {record.manager.name ??
              "Not assigned"}
          </dd>
        </div>

        <div>
          <dt>Project</dt>

          <dd>
            {record.project.name ??
              "Not assigned"}
          </dd>
        </div>

        <div>
          <dt>Buddy</dt>

          <dd>
            {record.poc.buddy.name ??
              "Not assigned"}
          </dd>
        </div>
      </dl>

      <div className="employee-admin-actions">
        <button
          type="button"
          onClick={() =>
            onView(record)
          }
        >
          <Eye size={16} />
          View
        </button>

        <button
          type="button"
          onClick={() =>
            onEditBuddy(record)
          }
        >
          <Pencil size={16} />
          Edit buddy
        </button>

        <button
          type="button"
          className={
            record.is_active
              ? "danger-action"
              : ""
          }
          onClick={() =>
            onToggleStatus(record)
          }
        >
          {record.is_active
            ? "Deactivate"
            : "Activate"}
        </button>
      </div>
    </article>
  );
}


export default function AdminOnboardingPage() {
  const {
    user,
    logout,
  } = useAuth();

  const [
    records,
    setRecords,
  ] = useState<
    EmployeeOnboardingRecord[]
  >([]);

  const [
    form,
    setForm,
  ] = useState<EmployeeFormState>(
    INITIAL_FORM
  );

  const [
    selectedRecord,
    setSelectedRecord,
  ] =
    useState<EmployeeOnboardingRecord | null>(
      null
    );

  const [
    buddyRecord,
    setBuddyRecord,
  ] =
    useState<EmployeeOnboardingRecord | null>(
      null
    );

  const [
    buddyName,
    setBuddyName,
  ] = useState("");

  const [
    buddyEmail,
    setBuddyEmail,
  ] = useState("");

  const [
    resetPassword,
    setResetPassword,
  ] = useState("");

  const [
    isLoading,
    setIsLoading,
  ] = useState(true);

  const [
    isSaving,
    setIsSaving,
  ] = useState(false);

  const [
    message,
    setMessage,
  ] = useState("");

  const [
    error,
    setError,
  ] = useState("");

  const roleLabel = useMemo(
    () =>
      getRoleLabel(
        user?.role ?? ""
      ),
    [user?.role]
  );


  const loadEmployees =
    useCallback(async () => {
      setIsLoading(true);
      setError("");

      try {
        const response =
          await listEmployeeOnboardingRecords(
            0,
            200
          );

        setRecords(
          response.items
        );
      } catch (requestError) {
        setError(
          getApiErrorMessage(
            requestError
          )
        );
      } finally {
        setIsLoading(false);
      }
    }, []);


  useEffect(() => {
    if (
      canManageOnboarding(
        user?.role
      )
    ) {
      loadEmployees();
    }
  }, [
    loadEmployees,
    user?.role,
  ]);


  if (
    !canManageOnboarding(
      user?.role
    )
  ) {
    return (
      <Navigate
        to="/chat"
        replace
      />
    );
  }


  function updateField(
    field: keyof EmployeeFormState,
    value: string | boolean
  ) {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));
  }


  async function handleCreate(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    const validationError =
      validateCreateForm(form);

    if (validationError) {
      setError(validationError);
      setMessage("");
      return;
    }

    setIsSaving(true);
    setError("");
    setMessage("");

    try {
      const created =
        await createEmployeeOnboardingRecord(
          buildCreatePayload(form)
        );

      setMessage(
        `${created.employee.full_name} was created successfully.`
      );

      setForm(INITIAL_FORM);

      await loadEmployees();
    } catch (requestError) {
      setError(
        getApiErrorMessage(
          requestError
        )
      );
    } finally {
      setIsSaving(false);
    }
  }


  function openBuddyEditor(
    record: EmployeeOnboardingRecord
  ) {
    setBuddyRecord(record);

    setBuddyName(
      record.poc.buddy.name ?? ""
    );

    setBuddyEmail(
      record.poc.buddy.email ?? ""
    );

    setResetPassword("");

    setError("");
    setMessage("");
  }


  async function saveBuddy() {
    if (!buddyRecord) {
      return;
    }

    const payload:
      UpdateEmployeeOnboardingRequest = {
        buddy_name:
          optionalValue(
            buddyName
          ),

        buddy_email:
          optionalValue(
            buddyEmail
          ),
    };

    if (resetPassword.trim()) {
      if (
        resetPassword.length < 12
      ) {
        setError(
          "The new temporary password must contain at least 12 characters."
        );

        return;
      }

      payload.new_temporary_password =
        resetPassword;
    }

    setIsSaving(true);
    setError("");
    setMessage("");

    try {
      const updated =
        await updateEmployeeOnboardingRecord(
          buddyRecord.user_id,
          payload
        );

      setMessage(
        `${updated.employee.full_name}'s onboarding details were updated.`
      );

      setBuddyRecord(null);
      setResetPassword("");

      await loadEmployees();
    } catch (requestError) {
      setError(
        getApiErrorMessage(
          requestError
        )
      );
    } finally {
      setIsSaving(false);
    }
  }


  async function toggleEmployeeStatus(
    record: EmployeeOnboardingRecord
  ) {
    const action =
      record.is_active
        ? "deactivate"
        : "activate";

    const confirmed =
      window.confirm(
        `Are you sure you want to ${action} ${record.employee.full_name}?`
      );

    if (!confirmed) {
      return;
    }

    setIsSaving(true);
    setError("");
    setMessage("");

    try {
      const updated =
        await updateEmployeeOnboardingRecord(
          record.user_id,
          {
            is_active:
              !record.is_active,
          }
        );

      setMessage(
        `${updated.employee.full_name} is now ${
          updated.is_active
            ? "active"
            : "inactive"
        }.`
      );

      await loadEmployees();
    } catch (requestError) {
      setError(
        getApiErrorMessage(
          requestError
        )
      );
    } finally {
      setIsSaving(false);
    }
  }


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

          <Link to="/onboarding">
            <Briefcase size={18} />
            My Onboarding
          </Link>

          <Link to="/tax">
            <Calculator size={18} />
            Tax Calculator
          </Link>

          <Link
            className="active"
            to="/admin/onboarding"
          >
            <Users size={18} />
            Employee Onboarding
          </Link>

          {isDocumentAdmin(
            user?.role
          ) && (
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
              {user?.full_name ??
                "User"}
            </strong>

            <span>{user?.email}</span>
          </div>
        </div>
      </aside>

      <section className="main-panel admin-onboarding-panel">
        <header className="topbar">
          <div>
            <h1>
              Employee Onboarding Management
            </h1>

            <p>
              Create employee accounts and
              manage organizational,
              project and onboarding
              assignments.
            </p>
          </div>

          <div className="admin-onboarding-header-actions">
            <button
              type="button"
              className="secondary-button"
              onClick={loadEmployees}
              disabled={isLoading}
            >
              <RefreshCw size={18} />
              Refresh
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

        {(message || error) && (
          <div
            className={`admin-alert ${
              error
                ? "error"
                : "success"
            }`}
            role={
              error
                ? "alert"
                : "status"
            }
          >
            {error ? (
              <AlertTriangle size={19} />
            ) : (
              <CheckCircle2 size={19} />
            )}

            <span>
              {error || message}
            </span>
          </div>
        )}

        <section className="admin-onboarding-layout">
          <form
            className="employee-create-card"
            onSubmit={handleCreate}
          >
            <div className="employee-create-heading">
              <UserPlus size={22} />

              <div>
                <span>
                  New employee
                </span>

                <h2>
                  Create onboarding profile
                </h2>
              </div>
            </div>

            <div className="employee-form-section">
              <h3>
                Employee account
              </h3>

              <div className="employee-form-grid">
                <label>
                  Employee ID *

                  <input
                    value={
                      form.employeeId
                    }
                    onChange={(event) =>
                      updateField(
                        "employeeId",
                        event.target.value
                      )
                    }
                    placeholder="EMP007"
                    required
                  />
                </label>

                <label>
                  Full name *

                  <input
                    value={
                      form.fullName
                    }
                    onChange={(event) =>
                      updateField(
                        "fullName",
                        event.target.value
                      )
                    }
                    placeholder="Employee name"
                    required
                  />
                </label>

                <label>
                  Company email *

                  <input
                    type="email"
                    value={form.email}
                    onChange={(event) =>
                      updateField(
                        "email",
                        event.target.value
                      )
                    }
                    placeholder="employee@company.com"
                    required
                  />
                </label>

                <label>
                  Temporary password *

                  <input
                    type="password"
                    value={
                      form.temporaryPassword
                    }
                    onChange={(event) =>
                      updateField(
                        "temporaryPassword",
                        event.target.value
                      )
                    }
                    required
                  />

                  <small>
                    Minimum 12 characters.
                  </small>
                </label>

                <label>
                  Designation

                  <input
                    value={
                      form.designation
                    }
                    onChange={(event) =>
                      updateField(
                        "designation",
                        event.target.value
                      )
                    }
                    placeholder="Data Analyst"
                  />
                </label>

                <label>
                  Location *

                  <input
                    value={
                      form.location
                    }
                    onChange={(event) =>
                      updateField(
                        "location",
                        event.target.value
                      )
                    }
                    required
                  />
                </label>
              </div>
            </div>

            <div className="employee-form-section">
              <h3>
                Organization
              </h3>

              <div className="employee-form-grid">
                <label>
                  Department *

                  <input
                    value={
                      form.department
                    }
                    onChange={(event) =>
                      updateField(
                        "department",
                        event.target.value
                      )
                    }
                    required
                  />
                </label>

                <label>
                  Business unit

                  <input
                    value={
                      form.businessUnit
                    }
                    onChange={(event) =>
                      updateField(
                        "businessUnit",
                        event.target.value
                      )
                    }
                  />
                </label>

                <label>
                  Manager name

                  <input
                    value={
                      form.managerName
                    }
                    onChange={(event) =>
                      updateField(
                        "managerName",
                        event.target.value
                      )
                    }
                  />
                </label>

                <label>
                  Manager email

                  <input
                    type="email"
                    value={
                      form.managerEmail
                    }
                    onChange={(event) =>
                      updateField(
                        "managerEmail",
                        event.target.value
                      )
                    }
                  />
                </label>
              </div>
            </div>

            <div className="employee-form-section">
              <h3>
                Project assignment
              </h3>

              <div className="employee-form-grid">
                <label>
                  Project name

                  <input
                    value={
                      form.projectName
                    }
                    onChange={(event) =>
                      updateField(
                        "projectName",
                        event.target.value
                      )
                    }
                  />
                </label>

                <label>
                  Project role

                  <input
                    value={
                      form.projectRole
                    }
                    onChange={(event) =>
                      updateField(
                        "projectRole",
                        event.target.value
                      )
                    }
                  />
                </label>

                <label>
                  Project start date

                  <input
                    type="date"
                    value={
                      form.projectStartDate
                    }
                    onChange={(event) =>
                      updateField(
                        "projectStartDate",
                        event.target.value
                      )
                    }
                  />
                </label>

                <label>
                  Onboarding status

                  <select
                    value={
                      form.onboardingStatus
                    }
                    onChange={(event) =>
                      updateField(
                        "onboardingStatus",
                        event.target.value
                      )
                    }
                  >
                    <option value="assigned">
                      Assigned
                    </option>

                    <option value="in_progress">
                      In progress
                    </option>

                    <option value="completed">
                      Completed
                    </option>

                    <option value="not_assigned">
                      Not assigned
                    </option>
                  </select>
                </label>
              </div>
            </div>

            <div className="employee-form-section">
              <h3>
                Shared POCs
              </h3>

              <p>
                HR and IT POCs are shared by
                department and location.
              </p>

              <div className="employee-form-grid">
                <label>
                  HR POC name

                  <input
                    value={
                      form.hrPocName
                    }
                    onChange={(event) =>
                      updateField(
                        "hrPocName",
                        event.target.value
                      )
                    }
                  />
                </label>

                <label>
                  HR POC email

                  <input
                    type="email"
                    value={
                      form.hrPocEmail
                    }
                    onChange={(event) =>
                      updateField(
                        "hrPocEmail",
                        event.target.value
                      )
                    }
                  />
                </label>

                <label>
                  IT POC name

                  <input
                    value={
                      form.itPocName
                    }
                    onChange={(event) =>
                      updateField(
                        "itPocName",
                        event.target.value
                      )
                    }
                  />
                </label>

                <label>
                  IT POC email

                  <input
                    type="email"
                    value={
                      form.itPocEmail
                    }
                    onChange={(event) =>
                      updateField(
                        "itPocEmail",
                        event.target.value
                      )
                    }
                  />
                </label>
              </div>
            </div>

            <div className="employee-form-section">
              <h3>
                Employee-specific buddy
              </h3>

              <div className="employee-form-grid">
                <label>
                  Buddy name

                  <input
                    value={
                      form.buddyName
                    }
                    onChange={(event) =>
                      updateField(
                        "buddyName",
                        event.target.value
                      )
                    }
                  />
                </label>

                <label>
                  Buddy email

                  <input
                    type="email"
                    value={
                      form.buddyEmail
                    }
                    onChange={(event) =>
                      updateField(
                        "buddyEmail",
                        event.target.value
                      )
                    }
                  />
                </label>
              </div>
            </div>

            <label className="employee-active-checkbox">
              <input
                type="checkbox"
                checked={
                  form.isActive
                }
                onChange={(event) =>
                  updateField(
                    "isActive",
                    event.target.checked
                  )
                }
              />

              Employee account is active
            </label>

            <div className="employee-form-actions">
              <button
                type="button"
                className="secondary-button"
                onClick={() =>
                  setForm(
                    INITIAL_FORM
                  )
                }
                disabled={isSaving}
              >
                <X size={18} />
                Clear
              </button>

              <button
                type="submit"
                disabled={isSaving}
              >
                <Plus size={18} />

                {isSaving
                  ? "Saving..."
                  : "Create employee"}
              </button>
            </div>
          </form>

          <section className="employee-list-card">
            <div className="employee-list-heading">
              <div>
                <span>
                  Employee directory
                </span>

                <h2>
                  Onboarding records
                </h2>
              </div>

              <strong>
                {records.length}
              </strong>
            </div>

            {isLoading ? (
              <div className="empty-state">
                Loading employees...
              </div>
            ) : records.length === 0 ? (
              <div className="empty-state">
                No employee onboarding
                records found.
              </div>
            ) : (
              <div className="employee-admin-grid">
                {records.map(
                  (record) => (
                    <EmployeeSummaryCard
                      key={
                        record.user_id
                      }
                      record={record}
                      onView={
                        setSelectedRecord
                      }
                      onEditBuddy={
                        openBuddyEditor
                      }
                      onToggleStatus={
                        toggleEmployeeStatus
                      }
                    />
                  )
                )}
              </div>
            )}
          </section>
        </section>
      </section>

      {selectedRecord && (
        <div
          className="employee-modal-backdrop"
          role="presentation"
          onClick={() =>
            setSelectedRecord(null)
          }
        >
          <section
            className="employee-modal"
            role="dialog"
            aria-modal="true"
            aria-label="Employee onboarding details"
            onClick={(event) =>
              event.stopPropagation()
            }
          >
            <div className="employee-modal-header">
              <div>
                <span>
                  Employee details
                </span>

                <h2>
                  {
                    selectedRecord
                      .employee
                      .full_name
                  }
                </h2>
              </div>

              <button
                type="button"
                onClick={() =>
                  setSelectedRecord(
                    null
                  )
                }
              >
                <X size={19} />
              </button>
            </div>

            <dl className="employee-modal-details">
              <div>
                <dt>Employee ID</dt>
                <dd>
                  {
                    selectedRecord
                      .employee
                      .employee_id
                  }
                </dd>
              </div>

              <div>
                <dt>Email</dt>
                <dd>
                  {
                    selectedRecord
                      .employee
                      .email
                  }
                </dd>
              </div>

              <div>
                <dt>Designation</dt>
                <dd>
                  {
                    selectedRecord
                      .employee
                      .designation ??
                    "Not assigned"
                  }
                </dd>
              </div>

              <div>
                <dt>Location</dt>
                <dd>
                  {
                    selectedRecord
                      .employee
                      .location ??
                    "Not assigned"
                  }
                </dd>
              </div>

              <div>
                <dt>Department</dt>
                <dd>
                  {
                    selectedRecord
                      .employee
                      .department ??
                    "Not assigned"
                  }
                </dd>
              </div>

              <div>
                <dt>Business unit</dt>
                <dd>
                  {
                    selectedRecord
                      .employee
                      .business_unit ??
                    "Not assigned"
                  }
                </dd>
              </div>

              <div>
                <dt>Manager</dt>
                <dd>
                  {
                    selectedRecord
                      .manager
                      .name ??
                    "Not assigned"
                  }
                </dd>
              </div>

              <div>
                <dt>Project</dt>
                <dd>
                  {
                    selectedRecord
                      .project
                      .name ??
                    "Not assigned"
                  }
                </dd>
              </div>

              <div>
                <dt>Project role</dt>
                <dd>
                  {
                    selectedRecord
                      .project
                      .role ??
                    "Not assigned"
                  }
                </dd>
              </div>

              <div>
                <dt>Start date</dt>
                <dd>
                  {formatDate(
                    selectedRecord
                      .project
                      .start_date
                  )}
                </dd>
              </div>

              <div>
                <dt>Buddy</dt>
                <dd>
                  {
                    selectedRecord
                      .poc
                      .buddy
                      .name ??
                    "Not assigned"
                  }
                </dd>
              </div>

              <div>
                <dt>Status</dt>
                <dd>
                  {formatStatus(
                    selectedRecord
                      .onboarding_status
                  )}
                </dd>
              </div>
            </dl>
          </section>
        </div>
      )}

      {buddyRecord && (
        <div
          className="employee-modal-backdrop"
          role="presentation"
          onClick={() =>
            setBuddyRecord(null)
          }
        >
          <section
            className="employee-modal compact"
            role="dialog"
            aria-modal="true"
            aria-label="Edit employee buddy"
            onClick={(event) =>
              event.stopPropagation()
            }
          >
            <div className="employee-modal-header">
              <div>
                <span>
                  Update employee
                </span>

                <h2>
                  {
                    buddyRecord
                      .employee
                      .full_name
                  }
                </h2>
              </div>

              <button
                type="button"
                onClick={() =>
                  setBuddyRecord(null)
                }
              >
                <X size={19} />
              </button>
            </div>

            <div className="employee-modal-form">
              <label>
                Buddy name

                <input
                  value={buddyName}
                  onChange={(event) =>
                    setBuddyName(
                      event.target.value
                    )
                  }
                />
              </label>

              <label>
                Buddy email

                <input
                  type="email"
                  value={buddyEmail}
                  onChange={(event) =>
                    setBuddyEmail(
                      event.target.value
                    )
                  }
                />
              </label>

              <label>
                Reset temporary password

                <input
                  type="password"
                  value={resetPassword}
                  onChange={(event) =>
                    setResetPassword(
                      event.target.value
                    )
                  }
                  placeholder="Leave blank to keep current password"
                />

                <small>
                  Minimum 12 characters.
                </small>
              </label>

              <button
                type="button"
                onClick={saveBuddy}
                disabled={isSaving}
              >
                <Save size={18} />

                {isSaving
                  ? "Saving..."
                  : "Save changes"}
              </button>
            </div>
          </section>
        </div>
      )}
    </main>
  );
}