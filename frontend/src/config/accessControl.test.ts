import {
  describe,
  expect,
  it,
} from "vitest";

import {
  getDefaultRoute,
  getRoleLabel,
  getVisibleNavigation,
  hasPermission,
  normalizeRole,
} from "./accessControl";


describe(
  "normalizeRole",
  () => {
    it(
      "normalizes valid admin roles",
      () => {
        expect(
          normalizeRole(
            "HR_ADMIN"
          )
        ).toBe("hr_admin");

        expect(
          normalizeRole(
            "super_admin"
          )
        ).toBe(
          "super_admin"
        );
      }
    );

    it(
      "defaults unknown roles to employee",
      () => {
        expect(
          normalizeRole(
            "unknown_role"
          )
        ).toBe("employee");

        expect(
          normalizeRole(null)
        ).toBe("employee");
      }
    );
  }
);


describe(
  "role permissions",
  () => {
    it(
      "allows employees to use employee modules",
      () => {
        expect(
          hasPermission(
            "employee",
            "chat:view"
          )
        ).toBe(true);

        expect(
          hasPermission(
            "employee",
            "onboarding:self:view"
          )
        ).toBe(true);

        expect(
          hasPermission(
            "employee",
            "tax:view"
          )
        ).toBe(true);
      }
    );

    it(
      "blocks employees from admin modules",
      () => {
        expect(
          hasPermission(
            "employee",
            "employees:manage"
          )
        ).toBe(false);

        expect(
          hasPermission(
            "employee",
            "documents:manage"
          )
        ).toBe(false);

        expect(
          hasPermission(
            "employee",
            "audit:view"
          )
        ).toBe(false);
      }
    );

    it(
      "allows HR Admin to manage employees and view audit logs",
      () => {
        expect(
          hasPermission(
            "hr_admin",
            "employees:manage"
          )
        ).toBe(true);

        expect(
          hasPermission(
            "hr_admin",
            "audit:view"
          )
        ).toBe(true);
      }
    );

    it(
      "blocks Finance and IT Admin from audit logs",
      () => {
        expect(
          hasPermission(
            "finance_admin",
            "audit:view"
          )
        ).toBe(false);

        expect(
          hasPermission(
            "it_admin",
            "audit:view"
          )
        ).toBe(false);
      }
    );

    it(
      "allows Super Admin to access all configured modules",
      () => {
        const permissions = [
          "chat:view",
          "onboarding:self:view",
          "tax:view",
          "documents:manage",
          "employees:manage",
          "audit:view",
        ] as const;

        for (
          const permission
          of permissions
        ) {
          expect(
            hasPermission(
              "super_admin",
              permission
            )
          ).toBe(true);
        }
      }
    );
  }
);


describe(
  "visible navigation",
  () => {
    it(
      "shows only employee navigation to employees",
      () => {
        const paths =
          getVisibleNavigation(
            "employee"
          ).map(
            (item) =>
              item.path
          );

        expect(paths).toEqual([
          "/chat",
          "/onboarding",
          "/tax",
        ]);
      }
    );

    it(
      "shows HR administration navigation to HR Admin",
      () => {
        const paths =
          getVisibleNavigation(
            "hr_admin"
          ).map(
            (item) =>
              item.path
          );

        expect(paths).toContain(
          "/admin/onboarding"
        );

        expect(paths).toContain(
          "/admin/documents"
        );

        expect(paths).toContain(
          "/admin/audit-logs"
        );
      }
    );

    it(
      "does not show audit navigation to Finance Admin",
      () => {
        const paths =
          getVisibleNavigation(
            "finance_admin"
          ).map(
            (item) =>
              item.path
          );

        expect(paths).not.toContain(
          "/admin/audit-logs"
        );
      }
    );
  }
);


describe(
  "default routes",
  () => {
    it(
      "redirects employees to chat",
      () => {
        expect(
          getDefaultRoute(
            "employee"
          )
        ).toBe("/chat");
      }
    );

    it(
      "redirects HR and Super Admin to employee management",
      () => {
        expect(
          getDefaultRoute(
            "hr_admin"
          )
        ).toBe(
          "/admin/onboarding"
        );

        expect(
          getDefaultRoute(
            "super_admin"
          )
        ).toBe(
          "/admin/onboarding"
        );
      }
    );

    it(
      "redirects Finance and IT Admin to documents",
      () => {
        expect(
          getDefaultRoute(
            "finance_admin"
          )
        ).toBe(
          "/admin/documents"
        );

        expect(
          getDefaultRoute(
            "it_admin"
          )
        ).toBe(
          "/admin/documents"
        );
      }
    );
  }
);


describe(
  "role labels",
  () => {
    it(
      "returns user-facing role labels",
      () => {
        expect(
          getRoleLabel(
            "hr_admin"
          )
        ).toBe("HR Admin");

        expect(
          getRoleLabel(
            "super_admin"
          )
        ).toBe(
          "Super Admin"
        );
      }
    );
  }
);