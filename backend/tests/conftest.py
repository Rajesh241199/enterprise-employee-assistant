import os


os.environ.setdefault(
    "APP_ENV",
    "test",
)

os.environ.setdefault(
    "APP_DEBUG",
    "false",
)

os.environ.setdefault(
    "DATABASE_URL",
    "sqlite+pysqlite:///:memory:",
)

os.environ.setdefault(
    "JWT_SECRET_KEY",
    (
        "test-jwt-secret-key-"
        "that-is-long-enough-for-tests"
    ),
)

os.environ.setdefault(
    "JWT_ALGORITHM",
    "HS256",
)

os.environ.setdefault(
    "ACCESS_TOKEN_EXPIRE_MINUTES",
    "60",
)

os.environ.setdefault(
    "APP_AUDIT_LOG_FILE",
    "tests/output/audit.jsonl",
)