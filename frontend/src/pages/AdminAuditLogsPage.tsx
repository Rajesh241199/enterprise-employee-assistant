import {
  AlertTriangle,
  Ban,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Clock3,
  RefreshCw,
  Search,
  ShieldCheck,
} from "lucide-react";
import {
  useEffect,
  useState,
  type FormEvent,
} from "react";

import {
  getAuditLogs,
  getAuditSummary,
} from "../api/audit";
import {
  getApiErrorMessage,
} from "../api/client";
import type {
  AuditLogFilters,
  AuditLogItem,
  AuditLogSummary,
} from "../types/audit";


const PAGE_LIMIT = 50;


const EMPTY_SUMMARY:
  AuditLogSummary = {
    total_events: 0,
    successful_events: 0,
    failed_events: 0,
    blocked_events: 0,
    events_last_24_hours: 0,
  };


function formatTimestamp(
  value: string
): string {
  const parsedDate =
    new Date(value);

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
      dateStyle: "medium",
      timeStyle: "medium",
    }
  ).format(parsedDate);
}


function formatEventType(
  value: string
): string {
  return value
    .replaceAll(".", " · ")
    .replaceAll("_", " ");
}


function getOutcomeClass(
  outcome: string
): string {
  const normalized =
    outcome.toLowerCase();

  if (
    normalized === "success"
  ) {
    return "success";
  }

  if (
    normalized === "blocked"
  ) {
    return "blocked";
  }

  return "failure";
}


function AuditSummaryCard({
  label,
  value,
  icon,
}: {
  label: string;
  value: number;
  icon: React.ReactNode;
}) {
  return (
    <article className="audit-summary-card">
      <div>
        {icon}
      </div>

      <span>{label}</span>

      <strong>
        {value.toLocaleString(
          "en-IN"
        )}
      </strong>
    </article>
  );
}


function AuditLogCard({
  item,
}: {
  item: AuditLogItem;
}) {
  return (
    <article className="audit-log-card">
      <div className="audit-log-card-heading">
        <div>
          <span className="audit-log-time">
            {formatTimestamp(
              item.timestamp
            )}
          </span>

          <h3>
            {formatEventType(
              item.event_type
            )}
          </h3>
        </div>

        <span
          className={
            `audit-outcome-pill ${
              getOutcomeClass(
                item.outcome
              )
            }`
          }
        >
          {item.outcome}
        </span>
      </div>

      <dl className="audit-log-details">
        <div>
          <dt>Actor</dt>

          <dd>
            {item.actor.email
              ?? "System"}
          </dd>
        </div>

        <div>
          <dt>Role</dt>

          <dd>
            {item.actor.role
              ?? "Not available"}
          </dd>
        </div>

        <div>
          <dt>Client IP</dt>

          <dd>
            {item.client.ip
              ?? "Not available"}
          </dd>
        </div>

        <div>
          <dt>Resource</dt>

          <dd>
            {item.resource.type
              ?? "Not available"}

            {item.resource.id
              ? ` #${item.resource.id}`
              : ""}
          </dd>
        </div>

        <div>
          <dt>Request ID</dt>

          <dd>
            {item.request_id
              ?? "Not available"}
          </dd>
        </div>
      </dl>

      <details className="audit-metadata">
        <summary>
          View event metadata
        </summary>

        <pre>
          {JSON.stringify(
            item.metadata,
            null,
            2
          )}
        </pre>
      </details>
    </article>
  );
}


export default function AdminAuditLogsPage() {
  const [
    items,
    setItems,
  ] = useState<AuditLogItem[]>(
    []
  );

  const [
    summary,
    setSummary,
  ] = useState<AuditLogSummary>(
    EMPTY_SUMMARY
  );

  const [
    total,
    setTotal,
  ] = useState(0);

  const [
    offset,
    setOffset,
  ] = useState(0);

  const [
    eventType,
    setEventType,
  ] = useState("");

  const [
    outcome,
    setOutcome,
  ] = useState("");

  const [
    actorEmail,
    setActorEmail,
  ] = useState("");

  const [
    actorRole,
    setActorRole,
  ] = useState("");

  const [
    resourceType,
    setResourceType,
  ] = useState("");

  const [
    activeFilters,
    setActiveFilters,
  ] = useState<AuditLogFilters>(
    {}
  );

  const [
    isLoading,
    setIsLoading,
  ] = useState(true);

  const [
    error,
    setError,
  ] = useState("");


  async function loadSummary() {
    const result =
      await getAuditSummary();

    setSummary(result);
  }


  async function loadLogs(
    requestedOffset: number,
    filters: AuditLogFilters
  ) {
    const result =
      await getAuditLogs(
        requestedOffset,
        PAGE_LIMIT,
        filters
      );

    setItems(result.items);
    setTotal(result.total);
    setOffset(result.offset);
  }


  async function loadPage(
    requestedOffset: number,
    filters: AuditLogFilters
  ) {
    setIsLoading(true);
    setError("");

    try {
      await Promise.all([
        loadSummary(),

        loadLogs(
          requestedOffset,
          filters
        ),
      ]);

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
    void loadPage(
      0,
      {}
    );
  }, []);


  function buildFilters():
    AuditLogFilters {
    const filters:
      AuditLogFilters = {};

    if (eventType.trim()) {
      filters.event_type =
        eventType.trim();
    }

    if (outcome) {
      filters.outcome =
        outcome;
    }

    if (actorEmail.trim()) {
      filters.actor_email =
        actorEmail.trim();
    }

    if (actorRole) {
      filters.actor_role =
        actorRole;
    }

    if (resourceType.trim()) {
      filters.resource_type =
        resourceType.trim();
    }

    return filters;
  }


  function handleFilter(
    event:
      FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    const filters =
      buildFilters();

    setActiveFilters(filters);

    void loadPage(
      0,
      filters
    );
  }


  function clearFilters() {
    setEventType("");
    setOutcome("");
    setActorEmail("");
    setActorRole("");
    setResourceType("");
    setActiveFilters({});

    void loadPage(
      0,
      {}
    );
  }


  const currentPage =
    Math.floor(
      offset / PAGE_LIMIT
    ) + 1;

  const totalPages =
    Math.max(
      1,
      Math.ceil(
        total / PAGE_LIMIT
      )
    );

  const hasPrevious =
    offset > 0;

  const hasNext =
    offset + PAGE_LIMIT
    < total;


  return (
    <main className="audit-page">
      <header className="audit-page-header">
        <div>
          <span>
            Security and compliance
          </span>

          <h1>
            Audit Logs
          </h1>

          <p>
            Review authentication,
            employee-management and
            document-administration
            activity.
          </p>
        </div>

        <button
          type="button"
          onClick={() =>
            void loadPage(
              offset,
              activeFilters
            )
          }
          disabled={isLoading}
        >
          <RefreshCw size={18} />

          Refresh
        </button>
      </header>

      <section className="audit-summary-grid">
        <AuditSummaryCard
          label="Total events"
          value={
            summary.total_events
          }
          icon={
            <ShieldCheck
              size={21}
            />
          }
        />

        <AuditSummaryCard
          label="Last 24 hours"
          value={
            summary
              .events_last_24_hours
          }
          icon={
            <Clock3 size={21} />
          }
        />

        <AuditSummaryCard
          label="Successful"
          value={
            summary
              .successful_events
          }
          icon={
            <CheckCircle2
              size={21}
            />
          }
        />

        <AuditSummaryCard
          label="Failed"
          value={
            summary.failed_events
          }
          icon={
            <AlertTriangle
              size={21}
            />
          }
        />

        <AuditSummaryCard
          label="Blocked"
          value={
            summary.blocked_events
          }
          icon={
            <Ban size={21} />
          }
        />
      </section>

      <form
        className="audit-filter-card"
        onSubmit={handleFilter}
      >
        <div className="audit-filter-grid">
          <label>
            Event type

            <input
              value={eventType}
              placeholder={
                "auth.login or document"
              }
              onChange={(event) =>
                setEventType(
                  event.target.value
                )
              }
            />
          </label>

          <label>
            Outcome

            <select
              value={outcome}
              onChange={(event) =>
                setOutcome(
                  event.target.value
                )
              }
            >
              <option value="">
                All outcomes
              </option>

              <option value="success">
                Success
              </option>

              <option value="failure">
                Failure
              </option>

              <option value="blocked">
                Blocked
              </option>
            </select>
          </label>

          <label>
            Actor email

            <input
              type="email"
              value={actorEmail}
              placeholder={
                "user@company.com"
              }
              onChange={(event) =>
                setActorEmail(
                  event.target.value
                )
              }
            />
          </label>

          <label>
            Actor role

            <select
              value={actorRole}
              onChange={(event) =>
                setActorRole(
                  event.target.value
                )
              }
            >
              <option value="">
                All roles
              </option>

              <option value="employee">
                Employee
              </option>

              <option value="hr_admin">
                HR Admin
              </option>

              <option value="finance_admin">
                Finance Admin
              </option>

              <option value="it_admin">
                IT Admin
              </option>

              <option value="super_admin">
                Super Admin
              </option>
            </select>
          </label>

          <label>
            Resource type

            <input
              value={resourceType}
              placeholder={
                "document or auth"
              }
              onChange={(event) =>
                setResourceType(
                  event.target.value
                )
              }
            />
          </label>
        </div>

        <div className="audit-filter-actions">
          <button
            type="button"
            className="secondary-button"
            onClick={clearFilters}
          >
            Clear filters
          </button>

          <button type="submit">
            <Search size={18} />

            Apply filters
          </button>
        </div>
      </form>

      {error && (
        <div
          className="error-box"
          role="alert"
        >
          {error}
        </div>
      )}

      <section className="audit-results-card">
        <div className="audit-results-heading">
          <div>
            <span>
              Activity history
            </span>

            <h2>
              {total.toLocaleString(
                "en-IN"
              )} events
            </h2>
          </div>

          <span>
            Page {currentPage}
            {" of "}
            {totalPages}
          </span>
        </div>

        {isLoading ? (
          <div className="empty-state">
            Loading audit records...
          </div>
        ) : items.length === 0 ? (
          <div className="empty-state">
            No audit records match
            the selected filters.
          </div>
        ) : (
          <div className="audit-log-list">
            {items.map((item) => (
              <AuditLogCard
                key={item.id}
                item={item}
              />
            ))}
          </div>
        )}

        <div className="audit-pagination">
          <button
            type="button"
            disabled={
              !hasPrevious
              || isLoading
            }
            onClick={() =>
              void loadPage(
                Math.max(
                  0,
                  offset - PAGE_LIMIT
                ),
                activeFilters
              )
            }
          >
            <ChevronLeft size={18} />

            Previous
          </button>

          <button
            type="button"
            disabled={
              !hasNext
              || isLoading
            }
            onClick={() =>
              void loadPage(
                offset + PAGE_LIMIT,
                activeFilters
              )
            }
          >
            Next

            <ChevronRight size={18} />
          </button>
        </div>
      </section>
    </main>
  );
}