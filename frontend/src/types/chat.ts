export type ChatAskRequest = {
  query: string;
  top_k: number;
  candidate_k: number;
  score_threshold: number;
  max_sources: number;
  use_reranking: boolean;
  use_query_rewriting: boolean;
  document_type: string | null;
  policy_name: string | null;
  department_owner: string | null;
  access_level: string | null;
  chunk_type: string | null;
};

export type ChatSource = {
  source_id?: number;
  score?: number;
  rerank_score?: number;
  document_id?: number;
  file_name?: string;
  policy_name?: string;
  document_type?: string;
  department_owner?: string;
  access_level?: string;
  page_number?: number;
  chunk_index?: number;
  chunk_type?: string;
  text_preview?: string;
};

export type ChatResponse = {
  query: string;
  rewritten_query?: string;
  route?: string;
  answer: string;
  confidence?: string;
  use_reranking?: boolean;
  use_query_rewriting?: boolean;
  filters?: {
    document_type?: string | null;
    policy_name?: string | null;
    department_owner?: string | null;
    requested_access_level?: string | null;
    enforced_access_levels?: string[];
    chunk_type?: string | null;
  };
  results_count?: number;
  sources?: ChatSource[];
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  response?: ChatResponse;
  errorType?: "security" | "rbac" | "general";
};