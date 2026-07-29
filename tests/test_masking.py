import pytest

from support_log_analyzer.masking import mask_sensitive_data


@pytest.mark.parametrize(
    ("raw", "placeholder"),
    [
        ("Contact engineer@example.test", "<EMAIL>"),
        ("Request from 192.0.2.42", "<IPV4>"),
        ("Authorization: Bearer demo-token-value-0001", "<BEARER_TOKEN>"),
        ("api_key=demo_api_key_0001", "<API_KEY>"),
        ("token sk_test_abcdefgh12345678", "<API_KEY>"),
        ("Call +1 (202) 555-0104", "<PHONE>"),
    ],
)
def test_masks_supported_sensitive_values(raw: str, placeholder: str) -> None:
    masked = mask_sensitive_data(raw)

    assert placeholder in masked
    assert raw.split()[-1] not in masked


def test_masks_multiple_values_in_one_message() -> None:
    message = "engineer@example.test at 198.51.100.8 used Bearer demo-token-value-0002"

    masked = mask_sensitive_data(message)

    assert masked.count("<EMAIL>") == 1
    assert masked.count("<IPV4>") == 1
    assert masked.count("<BEARER_TOKEN>") == 1


def test_keeps_non_sensitive_diagnostic_text() -> None:
    message = "Database timeout after 250 milliseconds"

    assert mask_sensitive_data(message) == message
