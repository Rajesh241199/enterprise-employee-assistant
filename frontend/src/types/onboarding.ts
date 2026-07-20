export type OnboardingContact = {
  name: string | null;
  email: string | null;
};

export type OnboardingEmployeeDetails = {
  employee_id: string;
  full_name: string;
  email: string;

  designation: string | null;
  location: string | null;
  department: string | null;
  business_unit: string | null;
};

export type OnboardingManagerDetails = {
  name: string | null;
  email: string | null;
};

export type OnboardingProjectDetails = {
  name: string | null;
  role: string | null;
  start_date: string | null;
};

export type OnboardingPOCDetails = {
  hr_poc: OnboardingContact;
  it_poc: OnboardingContact;
  buddy: OnboardingContact;
};

export type OnboardingProfileResponse = {
  employee: OnboardingEmployeeDetails;
  manager: OnboardingManagerDetails;
  project: OnboardingProjectDetails;
  poc: OnboardingPOCDetails;

  onboarding_status: string;
  profile_complete: boolean;
};