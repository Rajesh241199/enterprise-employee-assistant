import { apiClient } from "./client";
import type { OnboardingProfileResponse } from "../types/onboarding";


export async function getMyOnboardingProfile():
Promise<OnboardingProfileResponse> {
  const response =
    await apiClient.get<OnboardingProfileResponse>(
      "/api/onboarding/me"
    );

  return response.data;
}