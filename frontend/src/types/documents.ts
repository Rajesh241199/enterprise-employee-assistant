export type DocumentRecord = {
  id: number;
  file_name: string;
  document_type: string;
  policy_name: string;
  department_owner: string;
  access_level: string;
  status: string;
  uploaded_by?: number;
  extra_metadata?: Record<string, unknown>;
  created_at?: string;
};

export type UploadDocumentPayload = {
  file: File;
  document_type: string;
  policy_name: string;
  department_owner: string;
  access_level: string;
};

export type IndexDocumentResponse = {
  document_id: number;
  status: string;
  message: string;
  chunks_created?: number;
  domain_validation?: {
    domain_validation_passed?: boolean;
    domain_score?: number;
    matched_categories?: string[];
    matched_keywords?: string[];
    blocked_keywords?: string[];
    reason?: string;
  };
  security_scan?: {
    security_scan_passed?: boolean;
    chunks_scanned?: number;
    chunks_after_security_scan?: number;
    chunks_sanitized?: number;
  };
};