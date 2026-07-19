from decimal import Decimal


TaxSlab = tuple[Decimal | None, Decimal]


ZERO = Decimal("0")
ONE = Decimal("1")

CESS_RATE = Decimal("0.04")

OLD_STANDARD_DEDUCTION = Decimal("50000")
NEW_STANDARD_DEDUCTION = Decimal("75000")

OLD_REBATE_INCOME_LIMIT = Decimal("500000")
OLD_REBATE_MAXIMUM = Decimal("12500")

NEW_REBATE_INCOME_LIMIT = Decimal("1200000")
NEW_REBATE_MAXIMUM = Decimal("60000")

SECTION_80C_LIMIT = Decimal("150000")
SECTION_80CCD_1B_LIMIT = Decimal("50000")

# Version 1 accepts a user-confirmed eligible 80D amount and limits the
# combined self/family/parent deduction to ₹1,00,000.
SECTION_80D_LIMIT = Decimal("100000")

SELF_OCCUPIED_HOME_LOAN_INTEREST_LIMIT = Decimal("200000")

PRIVATE_OLD_EMPLOYER_NPS_RATE = Decimal("0.10")
GOVERNMENT_OLD_EMPLOYER_NPS_RATE = Decimal("0.14")
NEW_EMPLOYER_NPS_RATE = Decimal("0.14")

NEARLY_EQUAL_THRESHOLD = Decimal("1000")

CALCULATION_VERSION = "ty-2026-27-v1"


NEW_REGIME_SLABS: tuple[TaxSlab, ...] = (
    (Decimal("400000"), Decimal("0.00")),
    (Decimal("800000"), Decimal("0.05")),
    (Decimal("1200000"), Decimal("0.10")),
    (Decimal("1600000"), Decimal("0.15")),
    (Decimal("2000000"), Decimal("0.20")),
    (Decimal("2400000"), Decimal("0.25")),
    (None, Decimal("0.30")),
)


OLD_REGIME_SLABS_UNDER_60: tuple[TaxSlab, ...] = (
    (Decimal("250000"), Decimal("0.00")),
    (Decimal("500000"), Decimal("0.05")),
    (Decimal("1000000"), Decimal("0.20")),
    (None, Decimal("0.30")),
)


OLD_REGIME_SLABS_60_TO_79: tuple[TaxSlab, ...] = (
    (Decimal("300000"), Decimal("0.00")),
    (Decimal("500000"), Decimal("0.05")),
    (Decimal("1000000"), Decimal("0.20")),
    (None, Decimal("0.30")),
)


OLD_REGIME_SLABS_80_PLUS: tuple[TaxSlab, ...] = (
    (Decimal("500000"), Decimal("0.00")),
    (Decimal("1000000"), Decimal("0.20")),
    (None, Decimal("0.30")),
)