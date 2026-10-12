"""Model-call path tests. A stub client stands in for the API; no network is used.

These cover the code that runs on the first real prescription, including the
retry-once rule and the error messages.
"""

import base64
import io

import httpx
import pytest
from openai import APIConnectionError, APIStatusError, APITimeoutError, AuthenticationError
from PIL import Image

from app.config import MODEL_ID
from app.extract import build_messages, call_model, extract_text, run_extraction

PROMPT = "read this"
GOOD = '{"medicines":[{"name":"Dolo 650","unclear":false}],"notes":""}'
GOOD_TWO = '{"medicines":[{"name":"Amoxicillin","unclear":false}],"notes":""}'
BROKEN = "sorry, I cannot read this"


class _Message:
    def __init__(self, content):
        self.content = content


class _Choice:
    def __init__(self, content):
        self.message = _Message(content)


class _Completion:
    def __init__(self, content):
        self.choices = [_Choice(content)]


class _Completions:
    """Returns or raises one scripted item per call, and records the requests."""

    def __init__(self, script):
        self.script = list(script)
        self.requests = []

    def create(self, **kwargs):
        self.requests.append(kwargs)
        item = self.script.pop(0)
        if isinstance(item, BaseException):
            raise item
        return item


class _StubClient:
    def __init__(self, script):
        self.chat = type("_Chat", (), {"completions": _Completions(script)})()


def _jpeg(width=800, height=600) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (width, height), "white").save(buffer, format="JPEG")
    return buffer.getvalue()


def _http_status_error(status: int) -> APIStatusError:
    request = httpx.Request("POST", "https://integrate.api.nvidia.com/v1/chat/completions")
    response = httpx.Response(status, request=request)
    return APIStatusError("boom", response=response, body=None)


def test_valid_reply_is_parsed_into_the_schema():
    client = _StubClient([_Completion(GOOD)])
    result, raw, error = run_extraction(_jpeg(), PROMPT, client=client)
    assert error is None
    assert result.medicines[0].name == "Dolo 650"
    assert raw == GOOD


def test_the_request_uses_the_configured_model_and_low_temperature():
    client = _StubClient([_Completion(GOOD)])
    run_extraction(_jpeg(), PROMPT, client=client)
    sent = client.chat.completions.requests[0]
    assert sent["model"] == MODEL_ID
    assert sent["temperature"] == 0.0


def test_the_request_carries_the_image_as_a_base64_data_url():
    client = _StubClient([_Completion(GOOD)])
    run_extraction(_jpeg(), PROMPT, client=client)
    content = client.chat.completions.requests[0]["messages"][0]["content"]
    assert content[0]["type"] == "text"
    assert content[0]["text"] == PROMPT
    url = content[1]["image_url"]["url"]
    assert url.startswith("data:image/jpeg;base64,")
    decoded = base64.b64decode(url.split(",", 1)[1])
    assert decoded[:2] == b"\xff\xd8"


def test_a_fenced_reply_is_parsed_without_a_retry():
    client = _StubClient([_Completion(f"```json\n{GOOD}\n```")])
    result, _, error = run_extraction(_jpeg(), PROMPT, client=client)
    assert error is None
    assert result.medicines[0].name == "Dolo 650"
    assert len(client.chat.completions.requests) == 1


def test_broken_then_valid_reply_retries_once_and_succeeds():
    client = _StubClient([_Completion(BROKEN), _Completion(GOOD_TWO)])
    result, raw, error = run_extraction(_jpeg(), PROMPT, client=client)
    assert error is None
    assert result.medicines[0].name == "Amoxicillin"
    assert raw == GOOD_TWO
    assert len(client.chat.completions.requests) == 2


def test_broken_twice_reports_an_error_and_does_not_guess():
    client = _StubClient([_Completion(BROKEN), _Completion(BROKEN)])
    result, _, error = run_extraction(_jpeg(), PROMPT, client=client)
    assert result is None
    assert "retried once" in error
    assert len(client.chat.completions.requests) == 2


def test_the_raw_reply_is_returned_even_when_parsing_fails():
    client = _StubClient([_Completion(BROKEN), _Completion(BROKEN)])
    _, raw, _ = run_extraction(_jpeg(), PROMPT, client=client)
    assert raw == BROKEN


def test_an_empty_reply_is_an_error_not_an_empty_medicine_list():
    client = _StubClient([_Completion(""), _Completion("   ")])
    result, _, error = run_extraction(_jpeg(), PROMPT, client=client)
    assert result is None
    assert error == "empty response"


def test_a_401_names_the_key():
    client = _StubClient([_http_status_error(401)])
    result, _, error = run_extraction(_jpeg(), PROMPT, client=client)
    assert result is None
    assert "401" in error and "NVIDIA_API_KEY" in error


def test_a_403_names_the_key():
    client = _StubClient([_http_status_error(403)])
    _, _, error = run_extraction(_jpeg(), PROMPT, client=client)
    assert "403" in error and "NVIDIA_API_KEY" in error


def test_a_server_error_reports_the_status_code():
    client = _StubClient([_http_status_error(503)])
    _, _, error = run_extraction(_jpeg(), PROMPT, client=client)
    assert error == "The API returned HTTP 503."


def test_a_timeout_is_reported_readably():
    client = _StubClient([APITimeoutError(request=httpx.Request("POST", "https://x/y"))])
    _, _, error = run_extraction(_jpeg(), PROMPT, client=client)
    assert "did not answer within" in error


def test_a_connection_error_is_reported_readably():
    client = _StubClient([APIConnectionError(request=httpx.Request("POST", "https://x/y"))])
    _, _, error = run_extraction(_jpeg(), PROMPT, client=client)
    assert "Could not reach" in error


def test_an_error_response_does_not_trigger_the_retry():
    client = _StubClient([_http_status_error(500), _Completion(GOOD)])
    _, _, error = run_extraction(_jpeg(), PROMPT, client=client)
    assert error == "The API returned HTTP 500."
    assert len(client.chat.completions.requests) == 1


def test_a_large_image_is_shrunk_before_being_sent():
    client = _StubClient([_Completion(GOOD)])
    run_extraction(_jpeg(4000, 3000), PROMPT, client=client)
    url = client.chat.completions.requests[0]["messages"][0]["content"][1]["image_url"]["url"]
    sent = base64.b64decode(url.split(",", 1)[1])
    with Image.open(io.BytesIO(sent)) as image:
        assert max(image.size) == 1600


def test_a_broken_upload_is_reported_without_calling_the_model():
    client = _StubClient([_Completion(GOOD)])
    result, _, error = run_extraction(b"not an image", PROMPT, client=client)
    assert result is None
    assert "could not read the image" in error
    assert client.chat.completions.requests == []


def test_a_reply_that_does_not_match_the_schema_is_reported():
    client = _StubClient([_Completion('{"medicines": 5}'), _Completion('{"medicines": 5}')])
    result, _, error = run_extraction(_jpeg(), PROMPT, client=client)
    assert result is None
    assert "schema" in error


def test_extract_text_handles_a_content_list():
    text, error = extract_text(_Completion([{"type": "text", "text": "hello"}]))
    assert error is None
    assert text == "hello"


def test_extract_text_reports_no_choices():
    class _Empty:
        choices = []

    text, error = extract_text(_Empty())
    assert text == ""
    assert "no choices" in error


def test_build_messages_shape():
    messages = build_messages(PROMPT, _jpeg(100, 100))
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    assert len(messages[0]["content"]) == 2


def test_authentication_error_class_is_handled():
    request = httpx.Request("POST", "https://x/y")
    exc = AuthenticationError("bad key", response=httpx.Response(401, request=request), body=None)
    client = _StubClient([exc])
    _, error = call_model(client, PROMPT, _jpeg(100, 100))
    assert "401" in error