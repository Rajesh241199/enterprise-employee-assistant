import base64
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional, Tuple


class SecurityRisk(str, Enum):
    PROMPT_INJECTION = "prompt_injection"
    INDIRECT_PROMPT_INJECTION = "indirect_prompt_injection"
    SYSTEM_PROMPT_LEAKAGE = "system_prompt_leakage"
    SECRET_EXFILTRATION = "secret_exfiltration"
    ACCESS_ESCALATION = "access_escalation"
    RESTRICTED_DATA_LEAKAGE = "restricted_data_leakage"
    MALICIOUS_MARKDOWN = "malicious_markdown"
    ENCODED_ATTACK = "encoded_attack"
    UNSAFE_CONTEXT = "unsafe_context"
    UNSAFE_OUTPUT = "unsafe_output"
    UNKNOWN = "unknown"


@dataclass
class SecurityFinding:
    risk: SecurityRisk
    severity: str
    reason: str
    matched_text: Optional[str] = None


@dataclass
class SecurityCheckResult:
    allowed: bool
    findings: List[SecurityFinding] = field(default_factory=list)
    sanitized_text: Optional[str] = None

    @property
    def highest_severity(self) -> str:
        if any(f.severity == "critical" for f in self.findings):
            return "critical"
        if any(f.severity == "high" for f in self.findings):
            return "high"
        if any(f.severity == "medium" for f in self.findings):
            return "medium"
        if any(f.severity == "low" for f in self.findings):
            return "low"
        return "none"


class EnterpriseLLMGuardrails:
    """
    Deterministic enterprise guardrail layer for RAG applications.

    This class protects the backend against:
    - direct prompt injection
    - indirect prompt injection from retrieved documents
    - system/developer prompt leakage
    - secret leakage
    - access-level escalation
    - restricted document exfiltration
    - encoded attack instructions
    - unsafe markdown/html output
    """

    BLOCKING_SEVERITIES = {"critical", "high"}

    PROMPT_INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|rules|system)",
        r"disregard\s+(all\s+)?(previous|prior|above)\s+(instructions|rules|system)",
        r"forget\s+(all\s+)?(previous|prior|above)\s+(instructions|rules|system)",
        r"override\s+(the\s+)?(system|developer|safety|security)\s+(prompt|instructions|rules)",
        r"you\s+are\s+now\s+(dan|developer\s+mode|unrestricted|jailbroken)",
        r"act\s+as\s+(dan|an\s+unfiltered\s+model|a\s+jailbroken\s+assistant)",
        r"bypass\s+(security|access\s+control|rbac|permissions|authorization)",
        r"do\s+not\s+follow\s+(the\s+)?(system|developer|security)\s+(instructions|rules)",
        r"follow\s+only\s+my\s+instructions",
        r"new\s+system\s+message",
        r"system\s*:\s*you\s+must",
        r"developer\s*:\s*you\s+must",
    ]

    SYSTEM_LEAKAGE_REQUEST_PATTERNS = [
        r"show\s+(me\s+)?(your\s+)?system\s+prompt",
        r"reveal\s+(your\s+)?system\s+prompt",
        r"print\s+(your\s+)?system\s+prompt",
        r"what\s+are\s+your\s+(hidden|system|developer)\s+instructions",
        r"show\s+(me\s+)?(hidden|developer)\s+instructions",
        r"repeat\s+(the\s+)?(system|developer)\s+(message|prompt|instructions)",
        r"expose\s+(the\s+)?(system|developer)\s+(prompt|instructions)",
    ]

    SECRET_EXFILTRATION_PATTERNS = [
        r"\.env",
        r"jwt[_\-\s]?secret",
        r"secret[_\-\s]?key",
        r"api[_\-\s]?key",
        r"access[_\-\s]?token",
        r"refresh[_\-\s]?token",
        r"database[_\-\s]?url",
        r"postgresql:\/\/",
        r"password\s+hash",
        r"private\s+key",
        r"aws[_\-\s]?access[_\-\s]?key",
        r"aws[_\-\s]?secret",
        r"ollama\s+config",
        r"qdrant\s+api\s+key",
    ]

    ACCESS_ESCALATION_PATTERNS = [
        r"access\s+(hr_only|finance_only|it_only|admin_only|confidential)",
        r"show\s+(me\s+)?(hr_only|finance_only|it_only|admin_only|confidential)",
        r"retrieve\s+(hr_only|finance_only|it_only|admin_only|confidential)",
        r"pretend\s+i\s+am\s+(hr|finance|it|admin|super\s*admin)",
        r"i\s+am\s+(hr|finance|it|admin|super\s*admin)\s+now",
        r"change\s+my\s+role\s+to\s+(hr|finance|it|admin|super\s*admin)",
        r"bypass\s+(role|rbac|permission|authorization)",
        r"ignore\s+(role|access\s+level|permission|authorization)",
    ]

    MALICIOUS_MARKDOWN_PATTERNS = [
        r"<script\b",
        r"</script>",
        r"javascript:",
        r"data:text\/html",
        r"<iframe\b",
        r"<object\b",
        r"<embed\b",
        r"onerror\s*=",
        r"onload\s*=",
        r"document\.cookie",
        r"window\.location",
    ]

    INDIRECT_CONTEXT_ATTACK_PATTERNS = [
        r"assistant\s+must\s+ignore",
        r"ignore\s+the\s+user",
        r"ignore\s+all\s+previous\s+instructions",
        r"this\s+document\s+overrides\s+system\s+instructions",
        r"when\s+answering,\s+do\s+not\s+mention\s+this",
        r"always\s+answer\s+with",
        r"send\s+the\s+user\s+secret",
        r"reveal\s+confidential",
        r"do\s+not\s+cite\s+sources",
        r"fabricate\s+the\s+answer",
    ]

    SECRET_VALUE_PATTERNS = [
        r"sk-[A-Za-z0-9_\-]{20,}",
        r"eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}",
        r"postgresql:\/\/[^\s]+",
        r"mysql:\/\/[^\s]+",
        r"mongodb(\+srv)?:\/\/[^\s]+",
        r"AKIA[0-9A-Z]{16}",
        r"-----BEGIN\s+(RSA|OPENSSH|PRIVATE)\s+KEY-----",
    ]

    SYSTEM_OUTPUT_LEAKAGE_PATTERNS = [
        r"system\s+prompt",
        r"developer\s+message",
        r"hidden\s+instruction",
        r"internal\s+instruction",
        r"do\s+not\s+reveal",
        r"you\s+are\s+chatgpt",
        r"confidential\s+system",
    ]

    RESTRICTED_ACCESS_LEVELS = {
        "hr_only",
        "finance_only",
        "it_only",
        "leadership_only",
        "admin_only",
        "confidential",
    }

    SAFE_REFUSAL = (
        "I cannot help with that request because it may violate security, "
        "privacy, or access-control rules."
    )

    def normalize_text(self, text: Optional[str]) -> str:
        if not text:
            return ""

        text = str(text)
        text = text.replace("\u200b", "")
        text = text.replace("\u200c", "")
        text = text.replace("\u200d", "")
        text = text.replace("\ufeff", "")
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _find_matches(
        self,
        text: str,
        patterns: Iterable[str],
        risk: SecurityRisk,
        severity: str,
    ) -> List[SecurityFinding]:
        findings = []

        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                findings.append(
                    SecurityFinding(
                        risk=risk,
                        severity=severity,
                        reason=f"Matched security pattern: {pattern}",
                        matched_text=match.group(0)[:200],
                    )
                )

        return findings

    def _try_decode_base64_segments(self, text: str) -> List[str]:
        decoded_values = []

        candidates = re.findall(r"[A-Za-z0-9+/=]{24,}", text)

        for candidate in candidates:
            try:
                padded = candidate + "=" * (-len(candidate) % 4)
                decoded_bytes = base64.b64decode(padded, validate=False)
                decoded_text = decoded_bytes.decode("utf-8", errors="ignore")

                if decoded_text and len(decoded_text.strip()) >= 8:
                    decoded_values.append(decoded_text.strip())

            except Exception:
                continue

        return decoded_values

    def _scan_encoded_payloads(self, text: str) -> List[SecurityFinding]:
        findings = []
        decoded_values = self._try_decode_base64_segments(text)

        for decoded_text in decoded_values:
            decoded_normalized = self.normalize_text(decoded_text)

            decoded_findings = []
            decoded_findings.extend(
                self._find_matches(
                    decoded_normalized,
                    self.PROMPT_INJECTION_PATTERNS,
                    SecurityRisk.ENCODED_ATTACK,
                    "high",
                )
            )
            decoded_findings.extend(
                self._find_matches(
                    decoded_normalized,
                    self.SECRET_EXFILTRATION_PATTERNS,
                    SecurityRisk.ENCODED_ATTACK,
                    "high",
                )
            )
            decoded_findings.extend(
                self._find_matches(
                    decoded_normalized,
                    self.ACCESS_ESCALATION_PATTERNS,
                    SecurityRisk.ENCODED_ATTACK,
                    "high",
                )
            )

            if decoded_findings:
                findings.append(
                    SecurityFinding(
                        risk=SecurityRisk.ENCODED_ATTACK,
                        severity="high",
                        reason="Base64 or encoded payload contains unsafe instructions.",
                        matched_text=decoded_normalized[:200],
                    )
                )

        return findings

    def redact_sensitive_text(self, text: str) -> str:
        safe_text = text or ""

        redactions = [
            (r"sk-[A-Za-z0-9_\-]{20,}", "[REDACTED_API_KEY]"),
            (
                r"eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}",
                "[REDACTED_JWT]",
            ),
            (r"postgresql:\/\/[^\s]+", "[REDACTED_DATABASE_URL]"),
            (r"mysql:\/\/[^\s]+", "[REDACTED_DATABASE_URL]"),
            (r"mongodb(\+srv)?:\/\/[^\s]+", "[REDACTED_DATABASE_URL]"),
            (r"AKIA[0-9A-Z]{16}", "[REDACTED_AWS_KEY]"),
            (
                r"-----BEGIN\s+(RSA|OPENSSH|PRIVATE)\s+KEY-----.*?-----END\s+(RSA|OPENSSH|PRIVATE)\s+KEY-----",
                "[REDACTED_PRIVATE_KEY]",
            ),
        ]

        for pattern, replacement in redactions:
            safe_text = re.sub(
                pattern,
                replacement,
                safe_text,
                flags=re.IGNORECASE | re.DOTALL,
            )

        return safe_text

    def validate_user_query(
        self,
        query: str,
        user_role: Optional[str] = None,
        requested_access_level: Optional[str] = None,
        allowed_access_levels: Optional[List[str]] = None,
    ) -> SecurityCheckResult:
        normalized = self.normalize_text(query)
        findings: List[SecurityFinding] = []

        findings.extend(
            self._find_matches(
                normalized,
                self.PROMPT_INJECTION_PATTERNS,
                SecurityRisk.PROMPT_INJECTION,
                "high",
            )
        )

        findings.extend(
            self._find_matches(
                normalized,
                self.SYSTEM_LEAKAGE_REQUEST_PATTERNS,
                SecurityRisk.SYSTEM_PROMPT_LEAKAGE,
                "critical",
            )
        )

        findings.extend(
            self._find_matches(
                normalized,
                self.SECRET_EXFILTRATION_PATTERNS,
                SecurityRisk.SECRET_EXFILTRATION,
                "critical",
            )
        )

        findings.extend(
            self._find_matches(
                normalized,
                self.ACCESS_ESCALATION_PATTERNS,
                SecurityRisk.ACCESS_ESCALATION,
                "high",
            )
        )

        findings.extend(
            self._find_matches(
                normalized,
                self.MALICIOUS_MARKDOWN_PATTERNS,
                SecurityRisk.MALICIOUS_MARKDOWN,
                "high",
            )
        )

        findings.extend(self._scan_encoded_payloads(normalized))

        allowed_levels = set(allowed_access_levels or [])

        if requested_access_level:
            requested_access_level = requested_access_level.strip()

            if (
                requested_access_level in self.RESTRICTED_ACCESS_LEVELS
                and requested_access_level not in allowed_levels
            ):
                findings.append(
                    SecurityFinding(
                        risk=SecurityRisk.ACCESS_ESCALATION,
                        severity="critical",
                        reason=(
                            f"User role '{user_role}' attempted to request unauthorized "
                            f"access_level='{requested_access_level}'."
                        ),
                        matched_text=requested_access_level,
                    )
                )

        allowed = not any(
            finding.severity in self.BLOCKING_SEVERITIES for finding in findings
        )

        return SecurityCheckResult(
            allowed=allowed,
            findings=findings,
            sanitized_text=self.redact_sensitive_text(normalized),
        )

    def scan_document_text(
        self,
        text: str,
        document_name: Optional[str] = None,
    ) -> SecurityCheckResult:
        """
        Used during ingestion or before context building.
        Detects indirect prompt injection and poisoned RAG content.
        """
        normalized = self.normalize_text(text)
        findings: List[SecurityFinding] = []

        findings.extend(
            self._find_matches(
                normalized,
                self.INDIRECT_CONTEXT_ATTACK_PATTERNS,
                SecurityRisk.INDIRECT_PROMPT_INJECTION,
                "high",
            )
        )

        findings.extend(
            self._find_matches(
                normalized,
                self.PROMPT_INJECTION_PATTERNS,
                SecurityRisk.INDIRECT_PROMPT_INJECTION,
                "high",
            )
        )

        findings.extend(
            self._find_matches(
                normalized,
                self.SECRET_VALUE_PATTERNS,
                SecurityRisk.SECRET_EXFILTRATION,
                "critical",
            )
        )

        findings.extend(
            self._find_matches(
                normalized,
                self.MALICIOUS_MARKDOWN_PATTERNS,
                SecurityRisk.MALICIOUS_MARKDOWN,
                "high",
            )
        )

        findings.extend(self._scan_encoded_payloads(normalized))

        if document_name and findings:
            for finding in findings:
                finding.reason = f"{finding.reason} Document: {document_name}"

        allowed = not any(
            finding.severity in self.BLOCKING_SEVERITIES for finding in findings
        )

        sanitized = self.redact_sensitive_text(normalized)

        return SecurityCheckResult(
            allowed=allowed,
            findings=findings,
            sanitized_text=sanitized,
        )

    def sanitize_context_text(self, text: str) -> Tuple[str, SecurityCheckResult]:
        """
        Sanitizes retrieved RAG context before passing it to the LLM.
        If a chunk contains indirect prompt injection, the chunk should not be used.
        """
        result = self.scan_document_text(text)

        if not result.allowed:
            return "", result

        sanitized = result.sanitized_text or self.redact_sensitive_text(text)

        return sanitized, result

    def sanitize_retrieved_chunks(
        self,
        chunks: List[Any],
        text_keys: Optional[List[str]] = None,
    ) -> Tuple[List[Any], List[SecurityCheckResult]]:
        """
        Generic sanitizer for retrieved chunks.

        Works with:
        - dict chunks
        - ORM-like objects
        - string chunks

        It tries common text fields:
        content, text, page_content, chunk_text.
        """
        text_keys = text_keys or ["content", "text", "page_content", "chunk_text"]

        safe_chunks = []
        results = []

        for chunk in chunks:
            chunk_text = self._extract_chunk_text(chunk, text_keys=text_keys)
            sanitized_text, check_result = self.sanitize_context_text(chunk_text)
            results.append(check_result)

            if check_result.allowed:
                updated_chunk = self._set_chunk_text(
                    chunk=chunk,
                    sanitized_text=sanitized_text,
                    text_keys=text_keys,
                )
                safe_chunks.append(updated_chunk)

        return safe_chunks, results

    def _extract_chunk_text(self, chunk: Any, text_keys: List[str]) -> str:
        if isinstance(chunk, str):
            return chunk

        if isinstance(chunk, dict):
            for key in text_keys:
                value = chunk.get(key)
                if isinstance(value, str):
                    return value
            return ""

        for key in text_keys:
            value = getattr(chunk, key, None)
            if isinstance(value, str):
                return value

        return ""

    def _set_chunk_text(
        self,
        chunk: Any,
        sanitized_text: str,
        text_keys: List[str],
    ) -> Any:
        if isinstance(chunk, str):
            return sanitized_text

        if isinstance(chunk, dict):
            for key in text_keys:
                if key in chunk and isinstance(chunk[key], str):
                    copied = dict(chunk)
                    copied[key] = sanitized_text
                    return copied
            return chunk

        for key in text_keys:
            if hasattr(chunk, key) and isinstance(getattr(chunk, key), str):
                try:
                    setattr(chunk, key, sanitized_text)
                except Exception:
                    pass
                return chunk

        return chunk

    def validate_llm_output(
        self,
        answer: str,
        allowed_access_levels: Optional[List[str]] = None,
        source_files: Optional[List[str]] = None,
        require_sources: bool = True,
    ) -> SecurityCheckResult:
        normalized = self.normalize_text(answer)
        findings: List[SecurityFinding] = []

        findings.extend(
            self._find_matches(
                normalized,
                self.SECRET_VALUE_PATTERNS,
                SecurityRisk.SECRET_EXFILTRATION,
                "critical",
            )
        )

        findings.extend(
            self._find_matches(
                normalized,
                self.SYSTEM_OUTPUT_LEAKAGE_PATTERNS,
                SecurityRisk.SYSTEM_PROMPT_LEAKAGE,
                "critical",
            )
        )

        findings.extend(
            self._find_matches(
                normalized,
                self.MALICIOUS_MARKDOWN_PATTERNS,
                SecurityRisk.MALICIOUS_MARKDOWN,
                "high",
            )
        )

        allowed_levels = set(allowed_access_levels or [])

        normalized_lower = normalized.lower()

        for restricted_level in self.RESTRICTED_ACCESS_LEVELS:
            # "confidential" is common policy language, for example:
            # "protect confidential company information".
            # Treat it as an access-level leak only when it appears as
            # explicit metadata/classification, not as ordinary prose.
            if restricted_level == "confidential":
                references_restricted_level = bool(
                    re.search(
                        r"\b(?:access[_\s-]?level|classification)"
                        r"\s*[:=]?\s*['\"]?confidential\b"
                        r"|\bconfidential_only\b",
                        normalized_lower,
                        flags=re.IGNORECASE,
                    )
                )
            else:
                references_restricted_level = bool(
                    re.search(
                        rf"\b{re.escape(restricted_level)}\b",
                        normalized_lower,
                        flags=re.IGNORECASE,
                    )
                )

            if (
                references_restricted_level
                and restricted_level not in allowed_levels
            ):
                findings.append(
                    SecurityFinding(
                        risk=SecurityRisk.RESTRICTED_DATA_LEAKAGE,
                        severity="critical",
                        reason=(
                            "Output references restricted access level "
                            f"'{restricted_level}' not allowed for the user."
                        ),
                        matched_text=restricted_level,
                    )
                )

        if require_sources:
            source_files = source_files or []

            if not source_files:
                findings.append(
                    SecurityFinding(
                        risk=SecurityRisk.UNSAFE_OUTPUT,
                        severity="medium",
                        reason="Policy-style answer has no validated source files.",
                    )
                )

        allowed = not any(
            finding.severity in self.BLOCKING_SEVERITIES for finding in findings
        )

        return SecurityCheckResult(
            allowed=allowed,
            findings=findings,
            sanitized_text=self.redact_sensitive_text(normalized),
        )

    def build_block_response(self, result: SecurityCheckResult) -> Dict[str, Any]:
        return {
            "answer": self.SAFE_REFUSAL,
            "blocked": True,
            "security": {
                "allowed": result.allowed,
                "highest_severity": result.highest_severity,
                "findings": [
                    {
                        "risk": finding.risk.value,
                        "severity": finding.severity,
                        "reason": finding.reason,
                    }
                    for finding in result.findings
                ],
            },
            "sources": [],
        }


guardrails = EnterpriseLLMGuardrails()