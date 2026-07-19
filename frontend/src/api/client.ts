import axios, { AxiosError } from "axios";

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export const TOKEN_STORAGE_KEY =
  "employee_assistant_access_token";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000,
  headers: {
    "Content-Type": "application/json",
  },
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_STORAGE_KEY);

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

type ValidationErrorItem = {
  loc?: Array<string | number>;
  msg?: string;
};

function formatValidationErrors(
  detail: ValidationErrorItem[]
): string {
  return detail
    .map((item) => {
      const field = item.loc
        ?.filter((part) => part !== "body")
        .join(" → ");

      if (field && item.msg) {
        return `${field}: ${item.msg}`;
      }

      return item.msg || "Invalid input";
    })
    .join(" ");
}

export function getApiErrorMessage(
  error: unknown
): string {
  if (error instanceof AxiosError) {
    const data = error.response?.data;

    if (typeof data?.detail === "string") {
      return data.detail;
    }

    if (Array.isArray(data?.detail)) {
      return formatValidationErrors(data.detail);
    }

    if (typeof data?.detail?.message === "string") {
      return data.detail.message;
    }

    if (typeof data?.detail?.answer === "string") {
      return data.detail.answer;
    }

    if (error.code === "ECONNABORTED") {
      return "The request took too long. Please try again.";
    }

    if (!error.response) {
      return "The backend is not reachable. Please check the API connection.";
    }

    if (error.message) {
      return error.message;
    }
  }

  return "Something went wrong. Please try again.";
}