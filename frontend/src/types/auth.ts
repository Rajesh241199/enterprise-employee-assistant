export type UserRole =
  | "employee"
  | "hr_admin"
  | "finance_admin"
  | "it_admin"
  | "super_admin"
  | string;


export type LoginRequest = {
  email: string;
  password: string;
};


export type LoginResponse = {
  access_token: string;
  token_type: string;
};


export type UserProfile = {
  id: number;
  employee_id?: string;
  full_name: string;
  email: string;
  role: UserRole;
  location?: string;
  designation?: string;
  department?: string;
  must_change_password: boolean;
};


export type ChangePasswordRequest = {
  current_password: string;
  new_password: string;
  confirm_password: string;
};


export type ChangePasswordResponse = {
  message: string;
  must_change_password: boolean;
};