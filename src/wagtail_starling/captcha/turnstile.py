"""Cloudflare Turnstile — the canonical bot-gate form field.

Extracted from medan ``src/medan/turnstile.py`` (the superset of the two
consumer implementations): the widget renders the ``cf-turnstile`` container
the Turnstile script turns into a challenge; the browser posts the resulting
token under ``cf-turnstile-response``. The field verifies that token
server-side with the site secret. Three outcomes: the token is genuine (the
form is valid), the token is missing or rejected (the field errors), or the
verification endpoint gives no answer (the field errors too — closed,
never open, because the gate is all that keeps bots off a public form).

Settings (the one canonical name per key — consumers rename on adoption):

- ``TURNSTILE_SITE_KEY`` — the widget's site key.
- ``TURNSTILE_SECRET_KEY`` — the server-side secret. On Cloudflare's
  documented test secrets (the dev defaults) a missing token does NOT fail
  the form, so local form testing needs no challenge; a real secret keeps
  the gate mandatory. Unlike the third-party field one consumer ran, there
  is no env kill switch that removes both the widget and verification.

``_verify`` is the test seam: tests replace it with an always-pass stub, so
no test reaches the network. Tokens are single-use: a form re-render needs a
fresh widget (HTMX flows re-render the field); pages load the script through
``wagtail_starling/captcha/turnstile_script.html``.
"""

import httpx
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import translation
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

SITEVERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
RESPONSE_FIELD = "cf-turnstile-response"
VERIFY_TIMEOUT_SECONDS = 5.0

# Cloudflare's documented test secrets (always pass / always block / always
# challenge). When one is configured the endpoint cannot verify a real
# challenge — i.e. dev — so the field must not block local form testing.
_TEST_SECRETS = {
    "1x0000000000000000000000000000000AA",
    "2x0000000000000000000000000000000AA",
    "3x0000000000000000000000000000000AA",
}

# The language codes the widget accepts are two-letter; Django's active
# language may carry a region ("ja-jp"), which the widget would reject.
_WIDGET_LANGUAGES = {"en", "ja"}


def is_test_secret(secret):
    """Whether ``secret`` is one of Cloudflare's documented test secrets."""
    return secret in _TEST_SECRETS


def _siteverify(token, transport=None):
    """Ask the verification endpoint whether ``token`` is genuine.

    Raises ``httpx.HTTPError`` when the endpoint cannot be reached or
    answers with an error status — the caller decides what no answer
    means. A 200 whose body is not the expected JSON counts as rejected.
    """
    payload = {"secret": settings.TURNSTILE_SECRET_KEY, "response": token}
    with httpx.Client(
        timeout=VERIFY_TIMEOUT_SECONDS,
        transport=transport,
    ) as client:
        response = client.post(SITEVERIFY_URL, data=payload)
    response.raise_for_status()
    try:
        return bool(response.json().get("success"))
    except (ValueError, AttributeError):
        return False


# The seam tests replace. Looked up at call time, never bound early.
_verify = _siteverify


def widget_language():
    """The language the widget is told to use, or ``auto``."""
    active = (translation.get_language() or "").split("-")[0].lower()
    return active if active in _WIDGET_LANGUAGES else "auto"


class TurnstileWidget(forms.Widget):
    def render(self, name, value, attrs=None, renderer=None):
        return format_html(
            '<div class="cf-turnstile" data-sitekey="{}" data-language="{}"'
            ' data-theme="auto"></div>',
            settings.TURNSTILE_SITE_KEY,
            widget_language(),
        )

    def value_from_datadict(self, data, files, name):
        return data.get(RESPONSE_FIELD, "")

    def value_omitted_from_data(self, data, files, name):
        return RESPONSE_FIELD not in data


class TurnstileField(forms.Field):
    widget = TurnstileWidget
    default_error_messages = {
        "required": _("Please complete the verification challenge."),
        "invalid": _("Please complete the verification challenge."),
        "unavailable": _(
            "The verification could not be checked. Please try again.",
        ),
    }

    def __init__(self, **kwargs):
        kwargs.setdefault("label", "")
        # On the Cloudflare test secrets (dev defaults) the endpoint cannot
        # verify a real challenge, so an absent token must not block local
        # form testing; a real secret keeps the gate mandatory.
        kwargs.setdefault("required", not is_test_secret(settings.TURNSTILE_SECRET_KEY))
        super().__init__(**kwargs)

    def validate(self, value):
        super().validate(value)
        if not value:
            return
        try:
            genuine = _verify(value)
        except Exception:
            raise ValidationError(
                self.error_messages["unavailable"], code="unavailable"
            )
        if not genuine:
            raise ValidationError(
                self.error_messages["invalid"],
                code="invalid",
            )
