import type {
  OnboardingEmployeeDetails,
  OnboardingManagerDetails,
  OnboardingPOCDetails,
  OnboardingProjectDetails,
} from "./onboarding";


export type EmployeeOnboardingRecord = {
  user_id: number;
  is_active: boolean;
  role: string;

  employee: OnboardingEmployeeDetails;
  manager: OnboardingManagerDetails;
  project: OnboardingProjectDetails;
  poc: OnboardingPOCDetails;

  onboarding_status: string;
  profile_complete: boolean;
};


export type EmployeeOnboardingListResponse = {
  items: EmployeeOnboardingRecord[];
  total: number;
  offset: number;
  limit: number;
};


export type CreateEmployeeOnboardingRequest = {
  employee_id: string;
  full_name: string;
  email: string;
  temporary_password: string;

  designation: string | null;
  location: string;
  department: string;
  business_unit: string | null;

  manager_name: string | null;
  manager_email: string | null;

  project_name: string | null;
  project_role: string | null;
  project_start_date: string | null;

  onboarding_status: string;
  is_active: boolean;

  hr_poc_name: string | null;
  hr_poc_email: string | null;

  it_poc_name: string | null;
  it_poc_email: string | null;

  buddy_name: string | null;
  buddy_email: string | null;
};


export type UpdateEmployeeOnboardingRequest =
  Partial<{
    employee_id: string;
    full_name: string;
    email: string;

    new_temporary_password: string;

    designation: string | null;
    location: string;
    department: string;
    business_unit: string | null;

    manager_name: string | null;
    manager_email: string | null;

    project_name: string | null;
    project_role: string | null;
    project_start_date: string | null;

    onboarding_status: string;
    is_active: boolean;

    hr_poc_name: string | null;
    hr_poc_email: string | null;

    it_poc_name: string | null;
    it_poc_email: string | null;

    buddy_name: string | null;
    buddy_email: string | null;
  }>;