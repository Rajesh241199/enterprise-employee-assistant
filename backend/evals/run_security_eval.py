import csv
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import requests


BASE_URL = os.getenv("EVAL_BASE_URL", "http://127.0.0.1:8000")
EVAL_DIR = Path(__file__).resolve().parent
CASES_PATH = EVAL_DIR / "security_attack_cases.json"
REPORT_DIR = EVAL_DIR / "reports"


def login(email: str, password: str) -> str:
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={
            "email": email,
            "password": password,
        },
        timeout=30,
    )

    response.raise_for_status()
    data = response.json()

    token = data.get("access_token") or data.get("token")

    if not token:
        raise RuntimeError(f"No access token found for {email}: {data}")

    return token


def build_payload(test_case: dict[str, Any]) -> dict[str, Any]:
    return {
        "query": test_case["query"],
        "top_k": test_case.get("top_k", 5),
        "candidate_k": test_case.get("candidate_k", 10),
        "score_threshold": test_case.get("score_threshold", 0.35),
        "max_sources": test_case.get("max_sources", 2),
        "use_reranking": test_case.get("use_reranking", True),
        "use_query_rewriting": test_case.get("use_query_rewriting", True),
        "document_type": test_case.get("document_type"),
        "policy_name": test_case.get("policy_name"),
        "department_owner": test_case.get("department_owner"),
        "access_level": test_case.get("access_level"),
        "chunk_type": test_case.get("chunk_type"),
    }


def call_chat(token: str, payload: dict[str, Any]) -> requests.Response:
    return requests.post(
        f"{BASE_URL}/api/chat/ask",
        json=payload,
        headers={
            "Authorization": f"Bearer {token}",
        },
        timeout=180,
    )


def flatten_text(data: Any) -> str:
    """
    Flatten both JSON keys and values.

    Example:
    {"blocked": true, "risk": "prompt_injection"}

    Old evaluator only captured:
    "true prompt_injection"

    New evaluator captures:
    "blocked true risk prompt_injection"
    """
    if isinstance(data, dict):
        parts = []

        for key, value in data.items():
            parts.append(str(key))
            parts.append(flatten_text(value))

        return " ".join(parts)

    if isinstance(data, list):
        return " ".join(flatten_text(item) for item in data)

    return str(data)


def evaluate_case(
    test_case: dict[str, Any],
    token_cache: dict[str, str],
) -> dict[str, Any]:
    email = test_case["email"]

    if email not in token_cache:
        token_cache[email] = login(
            email=email,
            password=test_case["password"],
        )

    payload = build_payload(test_case)
    response = call_chat(
        token=token_cache[email],
        payload=payload,
    )

    try:
        response_json = response.json()
    except Exception:
        response_json = {
            "raw_response": response.text,
        }

    response_text = flatten_text(response_json).lower()

    expected_status = test_case["expected_status"]
    expected_keywords = test_case.get("expected_keywords", [])

    status_passed = response.status_code == expected_status

    missing_keywords = [
        keyword
        for keyword in expected_keywords
        if keyword.lower() not in response_text
    ]

    keywords_passed = len(missing_keywords) == 0
    overall_passed = status_passed and keywords_passed

    failure_reason_parts = []

    if not status_passed:
        failure_reason_parts.append(
            f"Expected status {expected_status}, got {response.status_code}"
        )

    if not keywords_passed:
        failure_reason_parts.append(
            f"Missing keywords: {missing_keywords}"
        )

    return {
        "id": test_case["id"],
        "user": test_case["user"],
        "query": test_case["query"],
        "expected_status": expected_status,
        "actual_status": response.status_code,
        "status_passed": status_passed,
        "keywords_passed": keywords_passed,
        "overall_passed": overall_passed,
        "failure_reason": " | ".join(failure_reason_parts),
        "response_preview": json.dumps(response_json, ensure_ascii=False)[:1000],
    }


def save_reports(results: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    json_path = REPORT_DIR / f"security_eval_report_{timestamp}.json"
    csv_path = REPORT_DIR / f"security_eval_report_{timestamp}.csv"

    with json_path.open("w", encoding="utf-8") as file:
        json.dump(
            {
                "summary": summary,
                "results": results,
            },
            file,
            indent=2,
            ensure_ascii=False,
        )

    fieldnames = [
        "id",
        "user",
        "query",
        "expected_status",
        "actual_status",
        "status_passed",
        "keywords_passed",
        "overall_passed",
        "failure_reason",
        "response_preview",
    ]

    with csv_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for result in results:
            writer.writerow(
                {
                    field: result.get(field)
                    for field in fieldnames
                }
            )

    print(f"JSON report: {json_path}")
    print(f"CSV report: {csv_path}")


def main() -> None:
    with CASES_PATH.open("r", encoding="utf-8") as file:
        test_cases = json.load(file)

    token_cache: dict[str, str] = {}
    results: list[dict[str, Any]] = []

    for test_case in test_cases:
        print(f"Running {test_case['id']}")

        try:
            result = evaluate_case(
                test_case=test_case,
                token_cache=token_cache,
            )
        except Exception as exc:
            result = {
                "id": test_case["id"],
                "user": test_case["user"],
                "query": test_case["query"],
                "expected_status": test_case.get("expected_status"),
                "actual_status": None,
                "status_passed": False,
                "keywords_passed": False,
                "overall_passed": False,
                "failure_reason": str(exc),
                "response_preview": "",
            }

        results.append(result)

        status = "PASSED" if result["overall_passed"] else "FAILED"
        print(f"  -> {status}")

    total = len(results)
    passed = sum(1 for result in results if result["overall_passed"])
    failed = total - passed
    pass_rate = round((passed / total) * 100, 2) if total else 0

    summary = {
        "total": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": pass_rate,
        "base_url": BASE_URL,
    }

    print()
    print("Security Evaluation Summary")
    print("===========================")
    print(f"Total: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Pass Rate: {pass_rate}%")

    if failed:
        print()
        print("Failed Cases")
        print("============")

        for result in results:
            if not result["overall_passed"]:
                print(f"{result['id']}: {result['failure_reason']}")
                print(f"Response preview: {result['response_preview']}")
                print()

    save_reports(results=results, summary=summary)

    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()