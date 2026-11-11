"""FormBuilder for the Wagtail form builder's captcha field types.

One builder, three field types an editor can pick on a host ``FormField``:
reCAPTCHA v2 (checkbox), reCAPTCHA v3 (invisible, with a per-field score
threshold) and Cloudflare Turnstile. Extracted from medan PR #601's
``CustomFormBuilder`` — which itself duplicates a builder male had shipped
for Turnstile alone; this module is the single canonical copy.

``django_recaptcha`` is imported lazily, inside the two ``create_recaptcha_*``
methods only: a consumer that just needs the Turnstile field (male's shape)
does not pay for — or install — the reCAPTCHA extra.

Hosts wire it on their own FormPage:

    from wagtail_starling.captcha.builder import CaptchaFormBuilder

    class FormPage(AbstractEmailForm):
        form_builder = CaptchaFormBuilder
"""

from django.utils.translation import gettext_lazy as _
from wagtail.contrib.forms.forms import FormBuilder

from wagtail_starling.captcha.turnstile import (
    TurnstileField,
    TurnstileWidget,
)

#: Choices appended to Wagtail's ``FORM_FIELD_CHOICES`` on the host
#: ``FormField`` (via ``CaptchaFormFieldMixin``).
CAPTCHA_FIELD_CHOICES = [
    ("recaptcha_v2", _("reCAPTCHA v2 (Checkbox)")),
    ("recaptcha_v3", _("reCAPTCHA v3 (Invisible)")),
    ("turnstile", _("Cloudflare Turnstile (Invisible)")),
]


def form_has_turnstile(form_class):
    """Whether the built form class actually carries a Turnstile field.

    The host template reads this to load the Turnstile script only on forms
    that use it.
    """
    return any(
        isinstance(field.widget, TurnstileWidget)
        for field in form_class.base_fields.values()
    )


class CaptchaFormBuilder(FormBuilder):
    """Wagtail form builder with reCAPTCHA v2/v3 and Turnstile support."""

    def create_recaptcha_v2_field(self, field, options):
        """Create reCAPTCHA v2 (checkbox) field."""
        from django_recaptcha.fields import ReCaptchaField
        from django_recaptcha.widgets import ReCaptchaV2Checkbox

        # Always use empty label - the label in database is just a placeholder for admin
        options["label"] = ""
        # Set required=False to avoid showing asterisk without label.
        # NB: django-recaptcha 4.1 force-sets required=True on the field, so
        # this stays inert (kept verbatim from the medan PR — its review
        # flagged it and left it as-is).
        options["required"] = False
        options["error_messages"] = {
            "required": _("Invalid data, please try again."),
            "captcha_invalid": _("Invalid data, please try again."),
            "captcha_error": _("Invalid data, please try again."),
        }
        return ReCaptchaField(widget=ReCaptchaV2Checkbox(), **options)

    def create_recaptcha_v3_field(self, field, options):
        """Create reCAPTCHA v3 (invisible) field with a per-field threshold."""
        from django_recaptcha.fields import ReCaptchaField
        from django_recaptcha.widgets import ReCaptchaV3

        # Get custom score threshold if set (a mixin-contributed column on
        # the host FormField — see CaptchaFormFieldMixin).
        score_threshold = getattr(field, "recaptcha_score_threshold", None)

        # Always use empty label - the label in database is just a placeholder for admin
        options["label"] = ""
        # Set required=False to avoid showing asterisk without label (v3
        # validates internally). Inert for the same django-recaptcha reason
        # as v2 above.
        options["required"] = False
        options["error_messages"] = {
            "required": _("Invalid data, please try again."),
            "captcha_invalid": _("Invalid data, please try again."),
            "captcha_error": _("Invalid data, please try again."),
        }

        widget_kwargs = {}
        if score_threshold is not None:
            widget_kwargs["required_score"] = score_threshold

        return ReCaptchaField(widget=ReCaptchaV3(**widget_kwargs), **options)

    def create_turnstile_field(self, field, options):
        """Create Cloudflare Turnstile (invisible) field."""
        # The label is never shown — the widget carries its own UI; the admin
        # row's required checkbox is ignored (Wagtail defaults it True),
        # because whether the gate is required is decided by TurnstileField:
        # real secret → the gate must gate; Cloudflare test secret (dev) →
        # tokens optional.
        options["label"] = ""
        options.pop("required", None)
        return TurnstileField(**options)

    def get_form_class(self):
        form_class = super().get_form_class()
        # The page template reads this to decide whether to load the
        # Turnstile script, so it loads only on forms that actually use it.
        form_class.has_turnstile = form_has_turnstile(form_class)
        return form_class
