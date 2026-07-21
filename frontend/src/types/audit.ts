export type AuditActor = {
  user_id: number | null;
  email: string | null;
  role: string | null;
};


export type AuditClient = {
  ip: string | null;
  user_agent: string | null;
};


export type AuditResource = {
  type: string | null;
  id: string | null;
};


export type AuditLogItem = {
  id: number;
  timestamp: string;
  event_type: string;
  outcome: string;
  request_id: string | null;

  actor: AuditActor;
  client: AuditClient;
  resource: AuditResource;

  metadata: Record<
    string,
    unknown
  >;
};


export type AuditLogListResponse = {
  items: AuditLogItem[];

  total: number;
  offset: number;
  limit: number;
};


export type AuditLogSummary = {
  total_events: number;
  successful_events: number;
  failed_events: number;
  blocked_events: number;
  events_last_24_hours: number;
};


export type AuditLogFilters = {
  event_type?: string;
  outcome?: string;
  actor_email?: string;
  actor_role?: string;
  resource_type?: string;
};