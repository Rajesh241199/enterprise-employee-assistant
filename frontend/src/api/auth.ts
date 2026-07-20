import { apiClient } from "./client";

import type {
  ChangePasswordRequest,
  ChangePasswordResponse,
  LoginRequest,
  LoginResponse,
  UserProfile,
} from "../types/auth";


export async function loginUser(
  payload: LoginRequest
): Promise<LoginResponse> {
  const response =
    await apiClient.post<LoginResponse>(
      "/api/auth/login",
      payload
    );

  return response.data;
}


export async function getCurrentUser():
  Promise<UserProfile> {
  const response =
    await apiClient.get<UserProfile>(
      "/api/auth/me"
    );

  return response.data;
}


export async function changePassword(
  payload: ChangePasswordRequest
): Promise<ChangePasswordResponse> {
  const response =
    await apiClient.post<ChangePasswordResponse>(
      "/api/auth/change-password",
      payload
    );

  return response.data;
}