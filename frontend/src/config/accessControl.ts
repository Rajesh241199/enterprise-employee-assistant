export type AppRole =
  | "employee"
  | "hr_admin"
  | "finance_admin"
  | "it_admin"
  | "super_admin";


export type AppPermission =
  | "chat:view"
  | "onboarding:self:view"
  | "tax:view"
  | "documents:manage"
  | "employees:manage"
  | "audit:view";


export type NavigationIcon =
  | "chat"
  | "onboarding"
  | "tax"
  | "employees"
  | "documents"
  | "audit";


export type NavigationItem = {
  label: string;
  path: string;
  permission: AppPermission;
  icon: NavigationIcon;
};


export const ROLE_LABELS:
  Record<AppRole, string> = {
    employee: "Employee",
    hr_admin: "HR Admin",
    finance_admin:
      "Finance Admin",
    it_admin: "IT Admin",
    super_admin: "Super Admin",
  };


const EMPLOYEE_PERMISSIONS:
  AppPermission[] = [
    "chat:view",
    "onboarding:self:view",
    "tax:view",
  ];


export const ROLE_PERMISSIONS:
  Record<
    AppRole,
    AppPermission[]
  > = {
    employee: [
      ...EMPLOYEE_PERMISSIONS,
    ],

    hr_admin: [
      ...EMPLOYEE_PERMISSIONS,
      "documents:manage",
      "employees:manage",
      "audit:view",
    ],

    finance_admin: [
      ...EMPLOYEE_PERMISSIONS,
      "documents:manage",
    ],

    it_admin: [
      ...EMPLOYEE_PERMISSIONS,
      "documents:manage",
    ],

    super_admin: [
      ...EMPLOYEE_PERMISSIONS,
      "documents:manage",
      "employees:manage",
      "audit:view",
    ],
  };


export const NAVIGATION_ITEMS:
  NavigationItem[] = [
    {
      label: "Chat",
      path: "/chat",
      permission: "chat:view",
      icon: "chat",
    },

    {
      label: "My Onboarding",
      path: "/onboarding",
      permission:
        "onboarding:self:view",
      icon: "onboarding",
    },

    {
      label: "Tax Calculator",
      path: "/tax",
      permission: "tax:view",
      icon: "tax",
    },

    {
      label:
        "Employee Onboarding",
      path:
        "/admin/onboarding",
      permission:
        "employees:manage",
      icon: "employees",
    },

    {
      label: "Documents",
      path:
        "/admin/documents",
      permission:
        "documents:manage",
      icon: "documents",
    },

    {
      label: "Audit Logs",
      path:
        "/admin/audit-logs",
      permission: "audit:view",
      icon: "audit",
    },
  ];


export function normalizeRole(
  role?: string | null
): AppRole {
  const normalizedRole =
    role?.trim().toLowerCase();

  if (
    normalizedRole
      === "hr_admin"
    || normalizedRole
      === "finance_admin"
    || normalizedRole
      === "it_admin"
    || normalizedRole
      === "super_admin"
  ) {
    return normalizedRole;
  }

  return "employee";
}


export function hasPermission(
  role:
    string | null | undefined,

  permission:
    AppPermission
): boolean {
  const normalizedRole =
    normalizeRole(role);

  return ROLE_PERMISSIONS[
    normalizedRole
  ].includes(permission);
}


export function getRoleLabel(
  role?: string | null
): string {
  return ROLE_LABELS[
    normalizeRole(role)
  ];
}


export function getVisibleNavigation(
  role?: string | null
): NavigationItem[] {
  return NAVIGATION_ITEMS.filter(
    (item) =>
      hasPermission(
        role,
        item.permission
      )
  );
}


export function getDefaultRoute(
  role?: string | null
): string {
  const normalizedRole =
    normalizeRole(role);

  if (
    normalizedRole
      === "hr_admin"
    || normalizedRole
      === "super_admin"
  ) {
    return "/admin/onboarding";
  }

  if (
    normalizedRole
      === "finance_admin"
    || normalizedRole
      === "it_admin"
  ) {
    return "/admin/documents";
  }

  return "/chat";
}