import { apiClient } from "./client";
import type {
  DocumentRecord,
  IndexDocumentResponse,
  UploadDocumentPayload,
} from "../types/documents";

export async function listDocuments(): Promise<DocumentRecord[]> {
  const response = await apiClient.get<DocumentRecord[]>("/api/documents");
  return response.data;
}

export async function uploadDocument(
  payload: UploadDocumentPayload
): Promise<DocumentRecord> {
  const formData = new FormData();

  formData.append("file", payload.file);
  formData.append("document_type", payload.document_type);
  formData.append("policy_name", payload.policy_name);
  formData.append("department_owner", payload.department_owner);
  formData.append("access_level", payload.access_level);

  const response = await apiClient.post<DocumentRecord>(
    "/api/documents/upload",
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }
  );

  return response.data;
}

export async function indexDocument(
  documentId: number,
  forceReindex = true
): Promise<IndexDocumentResponse> {
  const response = await apiClient.post<IndexDocumentResponse>(
    `/api/documents/${documentId}/index`,
    null,
    {
      params: {
        force_reindex: forceReindex,
      },
    }
  );

  return response.data;
}