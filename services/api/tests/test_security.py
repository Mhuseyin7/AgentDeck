from app.security import redact


def test_redacts_common_bearer_and_key_forms() -> None:
    assert "secret" not in redact("Authorization: Bearer secret")
    assert "abcd" not in redact("API_KEY=abcd")


def test_preserves_non_sensitive_output() -> None:
    assert redact("tests: 12 passed") == "tests: 12 passed"
