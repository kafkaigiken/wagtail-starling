"""The Turnstile form field: the one bot gate every public form carries.

Ported verbatim from medan ``src/medan/tests/test_turnstile.py`` (PR #601)
as the canonical characterization — only the import path changed. The field
reads the ``cf-turnstile-response`` token the widget posts and asks the
verification endpoint whether it is genuine. With a real secret configured a
missing or rejected token fails the form, and an endpoint that cannot be
reached fails it too (closed, never open). On Cloudflare's test secrets (the
dev defaults) the token is optional — local form testing must not be blocked.
``_verify`` is the seam the tests replace, so nothing reaches the network.
"""

import httpx
import pytest
from django import forms
from django.utils import translation

from wagtail_starling.captcha import turnstile
from wagtail_starling.captcha.turnstile import (
    RESPONSE_FIELD,
    TurnstileField,
    TurnstileWidget,
)


class GateForm(forms.Form):
    captcha = TurnstileField()


def test_widget_renders_site_key_and_language(settings):
    settings.TURNSTILE_SITE_KEY = "site-key-123"

    with translation.override("ja"):
        html = TurnstileWidget().render("captcha", None)

    assert 'class="cf-turnstile"' in html
    assert 'data-sitekey="site-key-123"' in html
    assert 'data-language="ja"' in html


def test_widget_reads_the_turnstile_response_field():
    widget = TurnstileWidget()

    posted = {RESPONSE_FIELD: "tok"}
    assert widget.value_from_datadict(posted, {}, "captcha") == "tok"
    assert widget.value_from_datadict({}, {}, "captcha") == ""


def test_missing_token_fails_before_any_verification(settings, monkeypatch):
    # A real secret keeps the gate mandatory even for an absent token. The
    # form class is built inside the test: a module-level one would freeze
    # the fields' required flag from import-time settings.
    settings.TURNSTILE_SECRET_KEY = "real-secret-not-a-test-key"
    calls = []
    monkeypatch.setattr(
        turnstile,
        "_verify",
        lambda token: calls.append(token) or True,
    )

    class Gate(forms.Form):
        captcha = TurnstileField()

    form = Gate({})

    assert not form.is_valid()
    assert "captcha" in form.errors
    assert calls == []


def test_missing_token_passes_on_dev_test_keys(monkeypatch):
    # Cloudflare's always-pass test secret is the dev marker: the endpoint
    # cannot verify a real challenge there, so no token must be needed.
    calls = []
    monkeypatch.setattr(
        turnstile,
        "_verify",
        lambda token: calls.append(token) or True,
    )

    class Gate(forms.Form):
        captcha = TurnstileField()

    form = Gate({})

    assert form.is_valid()
    assert calls == []


def test_rejected_token_fails_the_form(monkeypatch):
    monkeypatch.setattr(turnstile, "_verify", lambda token: False)

    form = GateForm({RESPONSE_FIELD: "bad"})

    assert not form.is_valid()
    assert form.errors["captcha"] == [
        "Please complete the verification challenge.",
    ]


def test_unreachable_endpoint_fails_closed(monkeypatch):
    def boom(token):
        raise httpx.ConnectError("down")

    monkeypatch.setattr(turnstile, "_verify", boom)

    form = GateForm({RESPONSE_FIELD: "tok"})

    assert not form.is_valid()
    assert form.errors["captcha"] == [
        "The verification could not be checked. Please try again."
    ]


def test_accepted_token_passes(monkeypatch):
    seen = []
    monkeypatch.setattr(
        turnstile,
        "_verify",
        lambda token: seen.append(token) or True,
    )

    form = GateForm({RESPONSE_FIELD: "good"})

    assert form.is_valid(), form.errors
    assert seen == ["good"]


@pytest.mark.parametrize("success", [True, False])
def test_siteverify_posts_secret_and_token(settings, success):
    settings.TURNSTILE_SECRET_KEY = "secret-xyz"
    requests = []

    def handler(request):
        requests.append(request)
        answer = {"success": success, "error-codes": []}
        return httpx.Response(200, json=answer)

    transport = httpx.MockTransport(handler)
    verdict = turnstile._siteverify("tok-1", transport=transport)

    assert verdict is success
    assert len(requests) == 1
    assert requests[0].url == turnstile.SITEVERIFY_URL
    body = requests[0].content.decode()
    assert "secret=secret-xyz" in body
    assert "response=tok-1" in body


def test_siteverify_raises_on_a_server_error():
    def handler(request):
        return httpx.Response(502, text="bad gateway")

    with pytest.raises(httpx.HTTPError):
        turnstile._siteverify("tok", transport=httpx.MockTransport(handler))


def test_siteverify_treats_a_non_json_answer_as_rejected():
    def handler(request):
        return httpx.Response(200, text="not json")

    transport = httpx.MockTransport(handler)
    assert turnstile._siteverify("tok", transport=transport) is False
