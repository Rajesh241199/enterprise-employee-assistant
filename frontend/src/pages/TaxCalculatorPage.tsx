import {
  AlertTriangle,
  Calculator,
  FileText,
  IndianRupee,
  Info,
  Lock,
  LogOut,
  MessageSquareText,
  RefreshCcw,
  ShieldCheck,
  TrendingDown,
  UserRound,
} from "lucide-react";
import {
  useState,
  type FormEvent,
} from "react";
import { Link } from "react-router-dom";

import { getApiErrorMessage } from "../api/client";
import { compareTaxRegimes } from "../api/tax";
import { useAuth } from "../context/AuthContext";
import type {
  AgeGroup,
  EmployerType,
  TaxComparisonRequest,
  TaxComparisonResponse,
  TaxRegimeBreakdown,
} from "../types/tax";
import {
  toAmount,
  validateTaxComparisonRequest,
} from "../utils/taxValidation";


type TaxFormState = {
  ageGroup: AgeGroup;
  employerType: EmployerType;

  annualGrossSalary: string;
  annualBasicSalary: string;

  annualHraReceived: string;
  annualRentPaid: string;
  isMetroCity: boolean;

  professionalTaxPaid: string;

  section80c: string;
  section80d: string;
  section80ccd1b: string;

  homeLoanInterest: string;
  otherOldRegimeDeductions: string;

  employerNpsContribution: string;
  otherTaxableIncome: string;
};


type AmountField =
  | "annualGrossSalary"
  | "annualBasicSalary"
  | "annualHraReceived"
  | "annualRentPaid"
  | "professionalTaxPaid"
  | "section80c"
  | "section80d"
  | "section80ccd1b"
  | "homeLoanInterest"
  | "otherOldRegimeDeductions"
  | "employerNpsContribution"
  | "otherTaxableIncome";


type NumberFieldProps = {
  label: string;
  value: string;
  helper?: string;
  required?: boolean;
  maximum?: number;
  onChange: (value: string) => void;
};


type RegimeCardProps = {
  title: string;
  breakdown: TaxRegimeBreakdown;
  recommended: boolean;
};


const INITIAL_FORM: TaxFormState = {
  ageGroup: "under_60",
  employerType: "private_or_other",

  annualGrossSalary: "",
  annualBasicSalary: "",

  annualHraReceived: "0",
  annualRentPaid: "0",
  isMetroCity: false,

  professionalTaxPaid: "0",

  section80c: "0",
  section80d: "0",
  section80ccd1b: "0",

  homeLoanInterest: "0",
  otherOldRegimeDeductions: "0",

  employerNpsContribution: "0",
  otherTaxableIncome: "0",
};


function NumberField({
  label,
  value,
  helper,
  required = false,
  maximum,
  onChange,
}: NumberFieldProps) {
  return (
    <label className="tax-field">
      <span>
        {label}

        {required && (
          <strong className="required-mark">
            *
          </strong>
        )}
      </span>

      <input
        type="number"
        min="0"
        max={maximum}
        step="1"
        inputMode="decimal"
        value={value}
        required={required}
        onChange={(event) =>
          onChange(event.target.value)
        }
      />

      {helper && <small>{helper}</small>}
    </label>
  );
}


function getRoleLabel(role: string): string {
  const labels: Record<string, string> = {
    employee: "Employee",
    hr_admin: "HR Admin",
    finance_admin: "Finance Admin",
    it_admin: "IT Admin",
    super_admin: "Super Admin",
  };

  return labels[role] ?? role;
}


function isAdminRole(role?: string): boolean {
  return [
    "hr_admin",
    "finance_admin",
    "it_admin",
    "super_admin",
  ].includes(role ?? "");
}


function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value);
}


function getRecommendationLabel(
  recommendation:
    TaxComparisonResponse["recommended_regime"]
): string {
  if (recommendation === "old_regime") {
    return "Old Tax Regime";
  }

  if (recommendation === "new_regime") {
    return "New Tax Regime";
  }

  return "Both regimes are nearly equal";
}


function RegimeCard({
  title,
  breakdown,
  recommended,
}: RegimeCardProps) {
  return (
    <article
      className={`tax-result-card ${
        recommended ? "recommended" : ""
      }`}
    >
      <div className="tax-result-card-header">
        <div>
          <span>Estimated calculation</span>
          <h3>{title}</h3>
        </div>

        {recommended && (
          <span className="recommended-badge">
            Recommended
          </span>
        )}
      </div>

      <div className="tax-total">
        <span>Estimated total tax</span>

        <strong>
          {formatCurrency(breakdown.total_tax)}
        </strong>
      </div>

      <dl className="tax-breakdown">
        <div>
          <dt>Gross salary</dt>

          <dd>
            {formatCurrency(
              breakdown.gross_salary
            )}
          </dd>
        </div>

        <div>
          <dt>Other taxable income</dt>

          <dd>
            {formatCurrency(
              breakdown.other_taxable_income
            )}
          </dd>
        </div>

        <div>
          <dt>Taxable income</dt>

          <dd>
            {formatCurrency(
              breakdown.taxable_income
            )}
          </dd>
        </div>

        <div>
          <dt>Standard deduction</dt>

          <dd>
            {formatCurrency(
              breakdown.standard_deduction
            )}
          </dd>
        </div>

        <div>
          <dt>HRA exemption</dt>

          <dd>
            {formatCurrency(
              breakdown.hra_exemption
            )}
          </dd>
        </div>

        <div>
          <dt>Professional tax deduction</dt>

          <dd>
            {formatCurrency(
              breakdown.professional_tax_deduction
            )}
          </dd>
        </div>

        <div>
          <dt>Chapter VI-A deductions</dt>

          <dd>
            {formatCurrency(
              breakdown.chapter_vi_a_deductions
            )}
          </dd>
        </div>

        <div>
          <dt>Home-loan interest</dt>

          <dd>
            {formatCurrency(
              breakdown.home_loan_interest_deduction
            )}
          </dd>
        </div>

        <div>
          <dt>Employer NPS deduction</dt>

          <dd>
            {formatCurrency(
              breakdown.employer_nps_deduction
            )}
          </dd>
        </div>

        <div>
          <dt>Tax before rebate</dt>

          <dd>
            {formatCurrency(
              breakdown.tax_before_rebate
            )}
          </dd>
        </div>

        <div>
          <dt>Rebate</dt>

          <dd>
            {formatCurrency(breakdown.rebate)}
          </dd>
        </div>

        <div>
          <dt>Marginal relief</dt>

          <dd>
            {formatCurrency(
              breakdown.marginal_relief
            )}
          </dd>
        </div>

        <div>
          <dt>Income tax after relief</dt>

          <dd>
            {formatCurrency(
              breakdown.income_tax_after_relief
            )}
          </dd>
        </div>

        <div>
          <dt>Health and education cess</dt>

          <dd>
            {formatCurrency(
              breakdown.health_and_education_cess
            )}
          </dd>
        </div>
      </dl>
    </article>
  );
}


export default function TaxCalculatorPage() {
  const { user, logout } = useAuth();

  const [form, setForm] =
    useState<TaxFormState>(INITIAL_FORM);

  const [result, setResult] =
    useState<TaxComparisonResponse | null>(
      null
    );

  const [error, setError] =
    useState<string | null>(null);

  const [isCalculating, setIsCalculating] =
    useState(false);

  const roleLabel = getRoleLabel(
    user?.role ?? ""
  );


  function updateAmount(
    field: AmountField,
    value: string
  ) {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));
  }


  function resetCalculator() {
    setForm(INITIAL_FORM);
    setResult(null);
    setError(null);
  }


  function buildRequest():
    TaxComparisonRequest {
    return {
      tax_year: "2026-27",
      age_group: form.ageGroup,
      employer_type: form.employerType,

      annual_gross_salary: toAmount(
        form.annualGrossSalary
      ),

      annual_basic_salary: toAmount(
        form.annualBasicSalary
      ),

      annual_hra_received: toAmount(
        form.annualHraReceived
      ),

      annual_rent_paid: toAmount(
        form.annualRentPaid
      ),

      is_metro_city: form.isMetroCity,

      professional_tax_paid: toAmount(
        form.professionalTaxPaid
      ),

      section_80c: toAmount(
        form.section80c
      ),

      section_80d: toAmount(
        form.section80d
      ),

      section_80ccd_1b: toAmount(
        form.section80ccd1b
      ),

      home_loan_interest_self_occupied:
        toAmount(form.homeLoanInterest),

      other_old_regime_deductions:
        toAmount(
          form.otherOldRegimeDeductions
        ),

      employer_nps_contribution:
        toAmount(
          form.employerNpsContribution
        ),

      other_taxable_income: toAmount(
        form.otherTaxableIncome
      ),

      has_business_income: false,
      has_special_rate_income: false,
      has_foreign_income: false,
    };
  }


  async function handleSubmit(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    const payload = buildRequest();

    const validationError =
      validateTaxComparisonRequest(payload);

    if (validationError) {
      setError(validationError);
      setResult(null);
      return;
    }

    setIsCalculating(true);
    setError(null);
    setResult(null);

    try {
      const comparison =
        await compareTaxRegimes(payload);

      setResult(comparison);
    } catch (requestError) {
      setError(
        getApiErrorMessage(requestError)
      );
    } finally {
      setIsCalculating(false);
    }
  }


  const oldRegimeRecommended =
    result?.recommended_regime ===
    "old_regime";

  const newRegimeRecommended =
    result?.recommended_regime ===
    "new_regime";


  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <ShieldCheck size={24} />

          <div>
            <strong>
              Internal Employee Assistant
            </strong>

            <span>
              Policy Knowledge Portal
            </span>
          </div>
        </div>

        <nav className="sidebar-nav">
          <Link to="/chat">
            <MessageSquareText size={18} />
            Chat
          </Link>

          <Link
            className="active"
            to="/tax"
          >
            <Calculator size={18} />
            Tax Calculator
          </Link>

          {isAdminRole(user?.role) && (
            <Link to="/admin/documents">
              <FileText size={18} />
              Documents
            </Link>
          )}
        </nav>

        <div className="access-card">
          <Lock size={18} />

          <div>
            <strong>Role access</strong>
            <span>{roleLabel}</span>
          </div>
        </div>

        <div className="user-card">
          <div className="avatar">
            <UserRound size={20} />
          </div>

          <div>
            <strong>
              {user?.full_name ?? "User"}
            </strong>

            <span>{user?.email}</span>
          </div>
        </div>
      </aside>

      <section className="main-panel tax-panel">
        <header className="topbar">
          <div>
            <h1>
              Tax Regime Comparison
            </h1>

            <p>
              Compare estimated old and new
              regime tax for Tax Year 2026–27.
            </p>
          </div>

          <button
            type="button"
            className="secondary-button"
            onClick={logout}
          >
            <LogOut size={18} />
            Logout
          </button>
        </header>

        <div className="privacy-notice">
          <ShieldCheck size={20} />

          <div>
            <strong>
              Privacy protected
            </strong>

            <span>
              Salary, rent, income and
              deduction values are used only
              for the current calculation.
              They are not saved in the
              application database or audit
              metadata.
            </span>
          </div>
        </div>

        {error && (
          <div
            className="tax-alert error"
            role="alert"
          >
            <AlertTriangle size={19} />
            <span>{error}</span>
          </div>
        )}

        <div className="tax-layout">
          <form
            className="tax-form-card"
            onSubmit={handleSubmit}
          >
            <section className="tax-form-section">
              <div className="tax-section-heading">
                <div>
                  <span>Section 1</span>
                  <h2>
                    Taxpayer profile
                  </h2>
                </div>

                <UserRound size={21} />
              </div>

              <div className="tax-form-grid">
                <label className="tax-field">
                  <span>Tax year</span>

                  <select
                    value="2026-27"
                    disabled
                  >
                    <option value="2026-27">
                      2026–27
                    </option>
                  </select>

                  <small>
                    Calculator rules are
                    versioned for this tax year.
                  </small>
                </label>

                <label className="tax-field">
                  <span>Age group</span>

                  <select
                    value={form.ageGroup}
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        ageGroup:
                          event.target
                            .value as AgeGroup,
                      }))
                    }
                  >
                    <option value="under_60">
                      Below 60 years
                    </option>

                    <option value="age_60_to_79">
                      60–79 years
                    </option>

                    <option value="age_80_plus">
                      80 years or above
                    </option>
                  </select>
                </label>

                <label className="tax-field">
                  <span>Employer type</span>

                  <select
                    value={
                      form.employerType
                    }
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        employerType:
                          event.target
                            .value as EmployerType,
                      }))
                    }
                  >
                    <option value="private_or_other">
                      Private or other employer
                    </option>

                    <option value="central_or_state_government">
                      Central or state
                      government
                    </option>
                  </select>
                </label>
              </div>
            </section>

            <section className="tax-form-section">
              <div className="tax-section-heading">
                <div>
                  <span>Section 2</span>
                  <h2>
                    Salary and income
                  </h2>
                </div>

                <IndianRupee size={21} />
              </div>

              <div className="tax-form-grid">
                <NumberField
                  label="Annual gross salary"
                  value={
                    form.annualGrossSalary
                  }
                  required
                  maximum={5_000_000}
                  helper="Total annual taxable salary before exemptions and deductions"
                  onChange={(value) =>
                    updateAmount(
                      "annualGrossSalary",
                      value
                    )
                  }
                />

                <NumberField
                  label="Annual basic salary"
                  value={
                    form.annualBasicSalary
                  }
                  maximum={5_000_000}
                  helper="Basic salary plus eligible dearness allowance used for HRA and employer NPS calculations"
                  onChange={(value) =>
                    updateAmount(
                      "annualBasicSalary",
                      value
                    )
                  }
                />

                <NumberField
                  label="Other taxable income"
                  value={
                    form.otherTaxableIncome
                  }
                  maximum={5_000_000}
                  helper="Interest or other ordinary-rate taxable income"
                  onChange={(value) =>
                    updateAmount(
                      "otherTaxableIncome",
                      value
                    )
                  }
                />

                <NumberField
                  label="Employer NPS contribution"
                  value={
                    form.employerNpsContribution
                  }
                  maximum={1_000_000}
                  helper="Employer contribution included in gross salary, where applicable"
                  onChange={(value) =>
                    updateAmount(
                      "employerNpsContribution",
                      value
                    )
                  }
                />
              </div>
            </section>

            <section className="tax-form-section">
              <div className="tax-section-heading">
                <div>
                  <span>Section 3</span>
                  <h2>HRA and rent</h2>
                </div>

                <Info size={21} />
              </div>

              <div className="tax-form-grid">
                <NumberField
                  label="Annual HRA received"
                  value={
                    form.annualHraReceived
                  }
                  maximum={5_000_000}
                  helper="Total HRA received during the tax year"
                  onChange={(value) =>
                    updateAmount(
                      "annualHraReceived",
                      value
                    )
                  }
                />

                <NumberField
                  label="Annual rent paid"
                  value={
                    form.annualRentPaid
                  }
                  maximum={5_000_000}
                  helper="Total eligible rent paid during the tax year"
                  onChange={(value) =>
                    updateAmount(
                      "annualRentPaid",
                      value
                    )
                  }
                />

                <label className="tax-checkbox-field">
                  <input
                    type="checkbox"
                    checked={
                      form.isMetroCity
                    }
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        isMetroCity:
                          event.target.checked,
                      }))
                    }
                  />

                  <span>
                    I live in an eligible metro
                    city for HRA calculation
                  </span>
                </label>
              </div>
            </section>

            <section className="tax-form-section">
              <div className="tax-section-heading">
                <div>
                  <span>Section 4</span>

                  <h2>
                    Old-regime deductions
                  </h2>
                </div>

                <TrendingDown size={21} />
              </div>

              <div className="tax-form-grid">
                <NumberField
                  label="Section 80C"
                  value={form.section80c}
                  maximum={500_000}
                  helper="PF, PPF, ELSS, life insurance and other eligible investments"
                  onChange={(value) =>
                    updateAmount(
                      "section80c",
                      value
                    )
                  }
                />

                <NumberField
                  label="Section 80D"
                  value={form.section80d}
                  maximum={200_000}
                  helper="Eligible medical-insurance and health-related deduction"
                  onChange={(value) =>
                    updateAmount(
                      "section80d",
                      value
                    )
                  }
                />

                <NumberField
                  label="Section 80CCD(1B)"
                  value={
                    form.section80ccd1b
                  }
                  maximum={200_000}
                  helper="Additional personal NPS deduction"
                  onChange={(value) =>
                    updateAmount(
                      "section80ccd1b",
                      value
                    )
                  }
                />

                <NumberField
                  label="Self-occupied home-loan interest"
                  value={
                    form.homeLoanInterest
                  }
                  maximum={1_000_000}
                  helper="Eligible interest on a self-occupied home loan"
                  onChange={(value) =>
                    updateAmount(
                      "homeLoanInterest",
                      value
                    )
                  }
                />

                <NumberField
                  label="Professional tax paid"
                  value={
                    form.professionalTaxPaid
                  }
                  maximum={20_000}
                  helper="Professional tax actually paid during the year"
                  onChange={(value) =>
                    updateAmount(
                      "professionalTaxPaid",
                      value
                    )
                  }
                />

                <NumberField
                  label="Other eligible deductions"
                  value={
                    form.otherOldRegimeDeductions
                  }
                  maximum={1_000_000}
                  helper="Enter only deductions whose eligibility has been confirmed"
                  onChange={(value) =>
                    updateAmount(
                      "otherOldRegimeDeductions",
                      value
                    )
                  }
                />
              </div>
            </section>

            <div className="tax-scope-warning">
              <AlertTriangle size={19} />

              <span>
                Version 1 supports resident
                salaried individuals with
                ordinary-rate income up to
                ₹50,00,000. It does not support
                business income, capital gains,
                crypto, lottery income, foreign
                income, surcharge or foreign-tax
                credit.
              </span>
            </div>

            <div className="tax-form-actions">
              <button
                type="button"
                className="tax-reset-button"
                onClick={resetCalculator}
                disabled={isCalculating}
              >
                <RefreshCcw size={18} />
                Reset
              </button>

              <button
                type="submit"
                className="tax-submit-button"
                disabled={isCalculating}
              >
                <Calculator size={18} />

                {isCalculating
                  ? "Calculating..."
                  : "Compare tax regimes"}
              </button>
            </div>
          </form>

          {result && (
            <section className="tax-results">
              <article className="recommendation-card">
                <div className="recommendation-icon">
                  <TrendingDown size={26} />
                </div>

                <div>
                  <span>
                    Recommended option
                  </span>

                  <h2>
                    {getRecommendationLabel(
                      result.recommended_regime
                    )}
                  </h2>

                  <p>{result.reason}</p>

                  <div className="saving-value">
                    <span>
                      Estimated annual saving
                    </span>

                    <strong>
                      {formatCurrency(
                        result
                          .estimated_annual_saving
                      )}
                    </strong>
                  </div>
                </div>
              </article>

              <div className="tax-results-grid">
                <RegimeCard
                  title="Old Tax Regime"
                  breakdown={
                    result.old_regime
                  }
                  recommended={
                    oldRegimeRecommended
                  }
                />

                <RegimeCard
                  title="New Tax Regime"
                  breakdown={
                    result.new_regime
                  }
                  recommended={
                    newRegimeRecommended
                  }
                />
              </div>

              <article className="tax-assumptions-card">
                <div className="tax-section-heading">
                  <div>
                    <span>
                      Calculation version:{" "}
                      {
                        result.calculation_version
                      }
                    </span>

                    <h2>
                      Assumptions and
                      limitations
                    </h2>
                  </div>

                  <Info size={21} />
                </div>

                <ul>
                  {result.assumptions.map(
                    (assumption) => (
                      <li key={assumption}>
                        {assumption}
                      </li>
                    )
                  )}
                </ul>

                <p className="tax-disclaimer">
                  {result.disclaimer}
                </p>
              </article>
            </section>
          )}
        </div>
      </section>
    </main>
  );
}