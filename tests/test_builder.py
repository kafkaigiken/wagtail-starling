"""Characterization for CaptchaFormBuilder and CaptchaFormFieldMixin.

Ported at package level from the two consumer suites that motivated the
extraction:

- male ``test_formpage_turnstile.py`` — the built turnstile field's label is
  empty (no <label> renders for it) and the ``turnstile`` choice exists with
  its admin label;
- medan PR #601 ``test_form_page.py`` — the builder's turnstile options
  handling and the ``has_turnstile`` form-class flag, plus the v3 score
  threshold flow.

The FormField/FormPage composition itself stays host-owned (medan's
2334-test suite re-runs it at consumption); here we pin the shared pieces.
"""

import sys
from unittest.mock import patch

from django import forms
from django.test import SimpleTestCase
from django_recaptcha.widgets import ReCaptchaV2Checkbox, ReCaptchaV3

from wagtail.contrib.forms.models import FORM_FIELD_CHOICES, AbstractFormField

from wagtail_starling.captcha.builder import (
    CAPTCHA_FIELD_CHOICES,
    CaptchaFormBuilder,
    form_has_turnstile,
)
from wagtail_starling.captcha.models import CaptchaFormFieldMixin
from wagtail_starling.captcha.turnstile import (
    RESPONSE_FIELD,
    TurnstileField,
    TurnstileWidget,
)


class StubField:
    """A minimal stand-in for a host FormField row on the builder path."""

    def __init__(self, field_type, clean_name, **attrs):
        self.field_type = field_type
        self.clean_name = clean_name
        self.label = attrs.get("label", "captcha")
        self.help_text = ""
        self.required = True
        self.default_value = ""
        self.choices = ""
        self.recaptcha_score_threshold = attrs.get("recaptcha_score_threshold")


class BuilderCharacterization(SimpleTestCase):
    def test_captcha_choices_are_the_three_field_types(self):
        values = dict(CAPTCHA_FIELD_CHOICES)
        assert values == {
            "recaptcha_v2": "reCAPTCHA v2 (Checkbox)",
            "recaptcha_v3": "reCAPTCHA v3 (Invisible)",
            "turnstile": "Cloudflare Turnstile (Invisible)",
        }

    def test_turnstile_field_gets_no_label_and_no_required_flag(self):
        # male's contract: the label is an admin placeholder only, and the
        # builder hands required to TurnstileField (which decides by secret).
        options = {"label": "captcha", "required": True, "help_text": ""}
        field = CaptchaFormBuilder([]).create_turnstile_field(
            StubField("turnstile", "captcha"), options
        )

        assert isinstance(field, TurnstileField)
        assert field.label == ""
        # Test settings carry Cloudflare's always-pass test secret (dev):
        # the gate downgrades to optional there.
        assert field.required is False

    def test_turnstile_field_is_mandatory_with_a_real_secret(self):
        with self.settings(TURNSTILE_SECRET_KEY="real-secret-not-a-test-key"):
            field = CaptchaFormBuilder([]).create_turnstile_field(
                StubField("turnstile", "captcha"),
                {"label": "captcha", "required": True},
            )

        assert field.required is True

    def test_turnstile_field_reads_its_response_field(self):
        field = CaptchaFormBuilder([]).create_turnstile_field(
            StubField("turnstile", "captcha"), {"label": "captcha"}
        )
        posted = {RESPONSE_FIELD: "tok", "other": "x"}
        assert field.widget.value_from_datadict(posted, {}, "captcha") == "tok"

    def test_recaptcha_v2_field_hides_the_label(self):
        field = CaptchaFormBuilder([]).create_recaptcha_v2_field(
            StubField("recaptcha_v2", "captcha"),
            {"label": "captcha", "required": True},
        )

        assert isinstance(field.widget, ReCaptchaV2Checkbox)
        assert field.label == ""
        assert field.error_messages["captcha_invalid"] == (
            "Invalid data, please try again."
        )

    def test_recaptcha_v3_threshold_comes_from_the_field(self):
        field = CaptchaFormBuilder([]).create_recaptcha_v3_field(
            StubField("recaptcha_v3", "captcha", recaptcha_score_threshold=0.8),
            {"label": "captcha", "required": True},
        )

        assert isinstance(field.widget, ReCaptchaV3)
        assert field.widget.required_score == 0.8

    def test_recaptcha_v3_without_threshold_uses_the_setting(self):
        # django-recaptcha's real default: no per-field threshold falls back
        # to settings.RECAPTCHA_REQUIRED_SCORE (not None).
        with self.settings(RECAPTCHA_REQUIRED_SCORE=0.55):
            field = CaptchaFormBuilder([]).create_recaptcha_v3_field(
                StubField("recaptcha_v3", "captcha", recaptcha_score_threshold=None),
                {"label": "captcha", "required": True},
            )

        assert isinstance(field.widget, ReCaptchaV3)
        assert field.widget.required_score == 0.55

    def test_turnstile_path_needs_no_recaptcha_dependency(self):
        # The recaptcha dependency rides as an extra; the Turnstile path
        # must work without it (male's adoption shape). A None entry in
        # sys.modules makes `import django_recaptcha.*` fail hard.
        saved = {}
        blocked = (
            "django_recaptcha",
            "django_recaptcha.fields",
            "django_recaptcha.widgets",
        )
        for name in blocked:
            saved[name] = sys.modules.pop(name, None)
            sys.modules[name] = None
        try:
            field = CaptchaFormBuilder([]).create_turnstile_field(
                StubField("turnstile", "captcha"), {"label": "captcha"}
            )
        finally:
            for name in blocked:
                sys.modules.pop(name, None)
                if saved[name] is not None:
                    sys.modules[name] = saved[name]

        assert isinstance(field, TurnstileField)

    def test_form_class_flags_turnstile_presence(self):
        builder = CaptchaFormBuilder(
            [StubField("turnstile", "captcha"), StubField("singleline", "name")]
        )
        form_class = builder.get_form_class()

        assert form_class.has_turnstile is True
        assert "captcha" in form_class.base_fields
        assert isinstance(form_class.base_fields["captcha"], TurnstileField)

        plain = CaptchaFormBuilder([StubField("singleline", "name")])
        assert plain.get_form_class().has_turnstile is False

    def test_form_has_turnstile_helper_matches_the_flag(self):
        form_class = CaptchaFormBuilder(
            [StubField("turnstile", "captcha")]
        ).get_form_class()

        assert form_has_turnstile(form_class) is True
        assert form_has_turnstile(forms.Form) is False


class HostFormField(CaptchaFormFieldMixin, AbstractFormField):
    """A concrete stand-in for a host FormField (no ParentalKey needed)."""

    class Meta:
        app_label = "wagtail_starling_captcha"


class MixinCharacterization(SimpleTestCase):
    def test_mixin_extends_wagtail_choices(self):
        choices = list(FORM_FIELD_CHOICES) + list(CAPTCHA_FIELD_CHOICES)
        field = HostFormField._meta.get_field("field_type")
        assert list(field.choices) == choices

    def test_concrete_field_carries_the_mixin_contract(self):
        field = HostFormField._meta.get_field("field_type")
        values = dict(field.choices)
        assert values["turnstile"] == "Cloudflare Turnstile (Invisible)"
        # male re-applied required_on_save after redefining field_type; the
        # mixin now does it once, canonically.
        assert field.required_on_save is True

        threshold = HostFormField._meta.get_field("recaptcha_score_threshold")
        assert threshold.null is True
        assert threshold.default == 0.5

    def test_mixin_panels_name_the_threshold_field(self):
        names = [p.field_name for p in CaptchaFormFieldMixin.panels]
        assert names == [
            "field_type",
            "label",
            "help_text",
            "required",
            "choices",
            "recaptcha_score_threshold",
        ]
