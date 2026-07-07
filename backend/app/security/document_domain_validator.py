from dataclasses import dataclass
from typing import Iterable

from app.db.models import Document
from app.rag.chunking import TextChunk


@dataclass
class DomainValidationResult:
    allowed: bool
    score: int
    matched_keywords: list[str]
    matched_categories: list[str]
    blocked_keywords: list[str]
    reason: str


class DocumentDomainValidator:
    """
    Validates whether an uploaded document belongs to the allowed knowledge
    domains for the Enterprise Employee Knowledge Assistant.

    Important enterprise rule:
    Metadata alone must NOT make a document valid.
    The actual extracted document content must be relevant.

    This prevents irrelevant but technically safe files from polluting:
    - PostgreSQL document_chunks
    - Qdrant vectors
    - RAG answers
    """

    MIN_DOMAIN_SCORE = 4

    ALLOWED_DOMAIN_KEYWORDS = {
        "hr_policy": [
            "human resources",
            "hr policy",
            "employee policy",
            "workplace policy",
            "employee handbook",
            "code of conduct",
            "employee lifecycle",
            "onboarding",
            "offboarding",
            "probation",
            "performance review",
            "manager approval",
            "reporting manager",
            "employment policy",
            "workplace conduct",
        ],
        "leave_holiday": [
            "leave policy",
            "privilege leave",
            "earned leave",
            "sick leave",
            "casual leave",
            "maternity leave",
            "paternity leave",
            "loss of pay",
            "holiday",
            "company holiday",
            "leave balance",
            "leave approval",
            "annual leave",
        ],
        "benefits": [
            "employee benefits",
            "benefits plan",
            "health insurance",
            "medical insurance",
            "wellness",
            "provident fund",
            "gratuity",
            "retirement benefit",
            "employee assistance",
            "workplace benefits",
            "insurance coverage",
        ],
        "compensation": [
            "compensation policy",
            "salary",
            "payroll",
            "bonus",
            "variable pay",
            "incentive",
            "annual increment",
            "salary revision",
            "pay structure",
            "ctc",
            "performance bonus",
        ],
        "expense_reimbursement": [
            "expense reimbursement",
            "reimbursement policy",
            "travel expense",
            "business travel",
            "meal expense",
            "lodging",
            "mileage",
            "receipt",
            "invoice",
            "claim submission",
            "finance approval",
            "reimbursable expenses",
        ],
        "it_security": [
            "it security",
            "information security",
            "access policy",
            "password policy",
            "multi-factor authentication",
            "mfa",
            "vpn",
            "privileged access",
            "account lockout",
            "device security",
            "remote access",
            "data protection",
            "user account",
        ],
        "events_poc": [
            "company event",
            "employee event",
            "townhall",
            "hr poc",
            "point of contact",
            "employee contact",
            "department contact",
            "office location",
            "employee communication",
        ],
    }

    GENERIC_EMPLOYEE_SIGNALS = [
        "employee",
        "employees",
        "company policy",
        "policy document",
        "approval",
        "manager",
        "department",
        "workplace",
        "organization policy",
    ]

    HARD_BLOCKLIST_TOPICS = [
        "missile",
        "missiles",
        "missile launching",
        "rocket force",
        "pla rocket force",
        "people's liberation army",
        "combat capabilities",
        "military-civilian integration",
        "national defense",
        "weapon",
        "weapons",
        "warfare",
        "military technology",
        "defense science",
        "combat",
        "force’s combat",
        "force's combat",
    ]

    SOFT_BLOCKLIST_TOPICS = [
        "political campaign",
        "sports match",
        "movie review",
        "celebrity news",
        "stock market news",
        "recipe",
        "travel blog",
        "random article",
    ]

    def normalize_text(self, text: str | None) -> str:
        if not text:
            return ""

        return " ".join(str(text).lower().split())

    def build_content_text(
        self,
        chunks: list[TextChunk],
        max_chars: int = 15000,
    ) -> str:
        """
        Builds validation text only from extracted document content.

        We intentionally do NOT include document metadata here because metadata
        can be user supplied and can accidentally or intentionally bypass domain checks.
        """
        chunk_text = " ".join(chunk.text for chunk in chunks)

        return self.normalize_text(chunk_text[:max_chars])

    def build_metadata_text(self, document: Document) -> str:
        """
        Metadata is used only for reporting/debugging, not for passing validation.
        """
        return self.normalize_text(
            " ".join(
                [
                    str(document.file_name or ""),
                    str(document.document_type or ""),
                    str(document.policy_name or ""),
                    str(document.department_owner or ""),
                    str(document.access_level or ""),
                ]
            )
        )

    def find_matches(
        self,
        text: str,
        keywords: Iterable[str],
    ) -> list[str]:
        matches = []

        for keyword in keywords:
            normalized_keyword = self.normalize_text(keyword)

            if normalized_keyword and normalized_keyword in text:
                matches.append(keyword)

        return sorted(set(matches))

    def validate(
        self,
        document: Document,
        chunks: list[TextChunk],
    ) -> DomainValidationResult:
        content_text = self.build_content_text(chunks=chunks)
        metadata_text = self.build_metadata_text(document=document)

        hard_blocklist_matches = self.find_matches(
            text=content_text,
            keywords=self.HARD_BLOCKLIST_TOPICS,
        )

        soft_blocklist_matches = self.find_matches(
            text=content_text,
            keywords=self.SOFT_BLOCKLIST_TOPICS,
        )

        matched_keywords: list[str] = []
        matched_categories: list[str] = []
        score = 0

        for category, keywords in self.ALLOWED_DOMAIN_KEYWORDS.items():
            category_matches = self.find_matches(
                text=content_text,
                keywords=keywords,
            )

            if category_matches:
                matched_categories.append(category)
                matched_keywords.extend(category_matches)

                score += 2
                score += min(len(category_matches), 3)

        generic_employee_signals = self.find_matches(
            text=content_text,
            keywords=self.GENERIC_EMPLOYEE_SIGNALS,
        )

        if generic_employee_signals:
            matched_keywords.extend(generic_employee_signals)

            # Generic terms help but cannot alone validate the document.
            score += min(len(generic_employee_signals), 2)

        matched_keywords = sorted(set(matched_keywords))
        matched_categories = sorted(set(matched_categories))

        if hard_blocklist_matches:
            return DomainValidationResult(
                allowed=False,
                score=score,
                matched_keywords=matched_keywords,
                matched_categories=matched_categories,
                blocked_keywords=hard_blocklist_matches,
                reason=(
                    "Document domain validation failed. "
                    "The document contains blocked non-employee-assistant topics: "
                    f"{hard_blocklist_matches[:10]}. "
                    "This knowledge base only accepts employee policy, HR, leave, benefits, "
                    "compensation, reimbursement, IT security, events, and POC documents."
                ),
            )

        if soft_blocklist_matches and score < self.MIN_DOMAIN_SCORE:
            return DomainValidationResult(
                allowed=False,
                score=score,
                matched_keywords=matched_keywords,
                matched_categories=matched_categories,
                blocked_keywords=soft_blocklist_matches,
                reason=(
                    "Document domain validation failed. "
                    "The document appears unrelated to employee policy content. "
                    f"Detected unrelated topics: {soft_blocklist_matches[:10]}"
                ),
            )

        if not matched_categories:
            return DomainValidationResult(
                allowed=False,
                score=score,
                matched_keywords=matched_keywords,
                matched_categories=matched_categories,
                blocked_keywords=[],
                reason=(
                    "Document domain validation failed. "
                    "The actual document content does not match any allowed employee-assistant domain. "
                    "Metadata alone is not sufficient for validation."
                ),
            )

        if score < self.MIN_DOMAIN_SCORE:
            return DomainValidationResult(
                allowed=False,
                score=score,
                matched_keywords=matched_keywords,
                matched_categories=matched_categories,
                blocked_keywords=[],
                reason=(
                    "Document domain validation failed. "
                    "The document does not contain enough employee-policy signals. "
                    "Allowed domains include HR policy, leave, holidays, benefits, compensation, "
                    "expense reimbursement, IT security, employee events, and POC guidance."
                ),
            )

        return DomainValidationResult(
            allowed=True,
            score=score,
            matched_keywords=matched_keywords,
            matched_categories=matched_categories,
            blocked_keywords=[],
            reason="Document content is relevant to the employee assistant knowledge base.",
        )


document_domain_validator = DocumentDomainValidator()