import {
  Briefcase,
  Calculator,
  FileText,
  Lock,
  LogOut,
  MessageSquareText,
  RefreshCw,
  ShieldCheck,
  Upload,
  UserRound,
} from "lucide-react";
import {
  useEffect,
  useMemo,
  useState,
  type FormEvent,
} from "react";
import { Link } from "react-router-dom";

import { getApiErrorMessage } from "../api/client";
import {
  indexDocument,
  listDocuments,
  uploadDocument,
} from "../api/documents";
import { useAuth } from "../context/AuthContext";
import type {
  DocumentRecord,
} from "../types/documents";


const accessLevels = [
  "all_employees",
  "hr_only",
  "finance_only",
  "it_only",
  "leadership_only",
  "admin_only",
  "confidential",
];


const documentTypes = [
  "benefits_policy",
  "leave_policy",
  "compensation_policy",
  "reimbursement_policy",
  "it_security_policy",
  "test_policy",
];


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


function isAdminRole(
  role?: string
): boolean {
  return [
    "hr_admin",
    "finance_admin",
    "it_admin",
    "super_admin",
  ].includes(role ?? "");
}


export default function AdminDocumentsPage() {
  const {
    user,
    logout,
  } = useAuth();

  const [
    documents,
    setDocuments,
  ] = useState<DocumentRecord[]>([]);

  const [
    isLoading,
    setIsLoading,
  ] = useState(true);

  const [
    isUploading,
    setIsUploading,
  ] = useState(false);

  const [
    indexingId,
    setIndexingId,
  ] = useState<number | null>(null);

  const [
    message,
    setMessage,
  ] = useState("");

  const [
    error,
    setError,
  ] = useState("");

  const [
    file,
    setFile,
  ] = useState<File | null>(null);

  const [
    documentType,
    setDocumentType,
  ] = useState("test_policy");

  const [
    policyName,
    setPolicyName,
  ] = useState(
    "Safe Test Policy 2026"
  );

  const [
    departmentOwner,
    setDepartmentOwner,
  ] = useState(
    "Human Resources"
  );

  const [
    accessLevel,
    setAccessLevel,
  ] = useState(
    "all_employees"
  );

  const roleLabel = useMemo(
    () =>
      getRoleLabel(user?.role ?? ""),
    [user?.role]
  );


  async function loadDocuments() {
    setIsLoading(true);
    setError("");

    try {
      const data =
        await listDocuments();

      setDocuments(data);
    } catch (requestError) {
      setError(
        getApiErrorMessage(
          requestError
        )
      );
    } finally {
      setIsLoading(false);
    }
  }


  useEffect(() => {
    loadDocuments();
  }, []);


  async function handleUpload(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    if (!file) {
      setError(
        "Please select a file."
      );

      return;
    }

    setIsUploading(true);
    setError("");
    setMessage("");

    try {
      const uploaded =
        await uploadDocument({
          file,
          document_type:
            documentType,
          policy_name:
            policyName,
          department_owner:
            departmentOwner,
          access_level:
            accessLevel,
        });

      setMessage(
        `Uploaded successfully: ${uploaded.file_name}`
      );

      setFile(null);

      await loadDocuments();
    } catch (requestError) {
      setError(
        getApiErrorMessage(
          requestError
        )
      );
    } finally {
      setIsUploading(false);
    }
  }


  async function handleIndex(
    documentId: number
  ) {
    setIndexingId(documentId);
    setError("");
    setMessage("");

    try {
      const response =
        await indexDocument(
          documentId,
          true
        );

      setMessage(
        response.message ||
          `Document ${documentId} indexed.`
      );

      await loadDocuments();
    } catch (requestError) {
      setError(
        getApiErrorMessage(
          requestError
        )
      );

      await loadDocuments();
    } finally {
      setIndexingId(null);
    }
  }


  if (!isAdminRole(user?.role)) {
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
              <MessageSquareText
                size={18}
              />
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
          </nav>

          <div className="access-card">
            <Lock size={18} />

            <div>
              <strong>
                Role access
              </strong>

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

              <span>
                {user?.email}
              </span>
            </div>
          </div>
        </aside>

        <section className="main-panel">
          <header className="topbar">
            <div>
              <h1>
                Access restricted
              </h1>

              <p>
                You do not have
                permission to access
                document administration.
              </p>
            </div>

            <button
              type="button"
              className="secondary-button"
              onClick={logout}
            >
              <LogOut size={18} />
              Logout
            </button>
          </header>

          <section className="placeholder-card">
            <div className="large-icon">
              <Lock size={36} />
            </div>

            <h2>
              Admin access required
            </h2>

            <p>
              Please log in as an HR
              Admin, Finance Admin, IT
              Admin, or Super Admin to
              manage policy documents.
            </p>

            <Link
              className="inline-action-button"
              to="/chat"
            >
              <MessageSquareText
                size={17}
              />
              Return to Chat
            </Link>
          </section>
        </section>
      </main>
    );
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
            <MessageSquareText
              size={18}
            />
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
            to="/admin/documents"
          >
            <FileText size={18} />
            Documents
          </Link>
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

      <section className="main-panel admin-panel">
        <header className="topbar">
          <div>
            <h1>
              Document Administration
            </h1>

            <p>
              Upload, validate, index and
              manage employee policy
              documents.
            </p>
          </div>

          <button
            type="button"
            className="secondary-button"
            onClick={logout}
          >
            <LogOut size={18} />
            Logout
          </button>
        </header>

        {(message || error) && (
          <div
            className={
              error
                ? "admin-alert error"
                : "admin-alert success"
            }
            role={
              error
                ? "alert"
                : "status"
            }
          >
            {error || message}
          </div>
        )}

        <section className="admin-layout">
          <form
            className="upload-card"
            onSubmit={handleUpload}
          >
            <div className="prompt-card-header">
              <Upload size={18} />

              <strong>
                Upload policy document
              </strong>
            </div>

            <label>
              File

              <input
                type="file"
                accept=".pdf,.txt,.docx,.csv,.xlsx,.png,.jpg,.jpeg"
                onChange={(event) =>
                  setFile(
                    event.target.files?.[0] ??
                      null
                  )
                }
              />
            </label>

            <label>
              Document type

              <select
                value={documentType}
                onChange={(event) =>
                  setDocumentType(
                    event.target.value
                  )
                }
              >
                {documentTypes.map(
                  (item) => (
                    <option
                      key={item}
                      value={item}
                    >
                      {item}
                    </option>
                  )
                )}
              </select>
            </label>

            <label>
              Policy name

              <input
                value={policyName}
                onChange={(event) =>
                  setPolicyName(
                    event.target.value
                  )
                }
                placeholder="Example: Leave Policy 2026"
              />
            </label>

            <label>
              Department owner

              <input
                value={departmentOwner}
                onChange={(event) =>
                  setDepartmentOwner(
                    event.target.value
                  )
                }
                placeholder="Example: Human Resources"
              />
            </label>

            <label>
              Access level

              <select
                value={accessLevel}
                onChange={(event) =>
                  setAccessLevel(
                    event.target.value
                  )
                }
              >
                {accessLevels.map(
                  (item) => (
                    <option
                      key={item}
                      value={item}
                    >
                      {item}
                    </option>
                  )
                )}
              </select>
            </label>

            <button
              type="submit"
              disabled={isUploading}
            >
              {isUploading
                ? "Uploading..."
                : "Upload document"}
            </button>
          </form>

          <section className="documents-card">
            <div className="documents-header">
              <div>
                <h2>
                  Indexed knowledge base
                </h2>

                <p>
                  {documents.length} document
                  records
                </p>
              </div>

              <button
                type="button"
                onClick={loadDocuments}
                disabled={isLoading}
              >
                <RefreshCw size={16} />

                {isLoading
                  ? "Refreshing..."
                  : "Refresh"}
              </button>
            </div>

            {isLoading ? (
              <div className="empty-state">
                Loading documents...
              </div>
            ) : documents.length === 0 ? (
              <div className="empty-state">
                No documents found.
              </div>
            ) : (
              <div className="documents-table-wrap">
                <table className="documents-table">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Policy</th>
                      <th>Type</th>
                      <th>Owner</th>
                      <th>Access</th>
                      <th>Status</th>
                      <th>Action</th>
                    </tr>
                  </thead>

                  <tbody>
                    {documents.map(
                      (document) => (
                        <tr
                          key={document.id}
                        >
                          <td>
                            {document.id}
                          </td>

                          <td>
                            <strong>
                              {document.policy_name ||
                                "Unnamed policy"}
                            </strong>

                            <span>
                              {
                                document.file_name
                              }
                            </span>
                          </td>

                          <td>
                            {
                              document.document_type
                            }
                          </td>

                          <td>
                            {document.department_owner ||
                              "Not specified"}
                          </td>

                          <td>
                            <span className="access-pill">
                              {
                                document.access_level
                              }
                            </span>
                          </td>

                          <td>
                            <span
                              className={`status-pill ${document.status}`}
                            >
                              {
                                document.status
                              }
                            </span>
                          </td>

                          <td>
                            <button
                              type="button"
                              className="table-action"
                              onClick={() =>
                                handleIndex(
                                  document.id
                                )
                              }
                              disabled={
                                indexingId ===
                                document.id
                              }
                            >
                              {indexingId ===
                              document.id
                                ? "Indexing..."
                                : "Index"}
                            </button>
                          </td>
                        </tr>
                      )
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </section>
      </section>
    </main>
  );
}