"""Abstract mixin for a host ``FormField`` model that carries captcha fields.

The host owns the model (the ``ParentalKey`` into its own FormPage) and the
migrations — this mixin only contributes what composes:

- the extended ``field_type`` choices (Wagtail's defaults + the three
  captcha types),
- the ``recaptcha_score_threshold`` column for reCAPTCHA v3,
- the admin panels, including the label help text explaining that a captcha
  row's label is an admin placeholder only.

Host-side use (the whole FormField collapses to this)::

    from modelcluster.fields import ParentalKey
    from wagtail.contrib.forms.models import AbstractFormField
    from wagtail_starling.captcha.models import CaptchaFormFieldMixin

    class FormField(CaptchaFormFieldMixin, AbstractFormField):
        page = ParentalKey("FormPage", on_delete=models.CASCADE,
                           related_name="form_fields")


The choice *values* never change (``recaptcha_v2`` / ``recaptcha_v3`` /
``turnstile``), so adopting the mixin alters only the admin labels — the
host migration for the choices comes from the host, as always.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel
from wagtail.contrib.forms.models import FORM_FIELD_CHOICES

from wagtail_starling.captcha.builder import CAPTCHA_FIELD_CHOICES

#: Label placeholder explanation shared by every consumer verbatim (proof the
#: copies had drifted: the same sentence was hand-maintained in two repos).
LABEL_HELP_TEXT = _(
    "Label displayed above the field. For captcha fields "
    "(reCAPTCHA / Turnstile), this won't be shown to users - "
    "you can use any placeholder text like 'captcha'."
)


class CaptchaFormFieldMixin(models.Model):
    """Extend a host AbstractFormField subclass with the captcha field types."""

    field_type = models.CharField(
        verbose_name=_("field type"),
        max_length=16,
        choices=list(FORM_FIELD_CHOICES) + list(CAPTCHA_FIELD_CHOICES),
    )
    # field_type must be populated for previews to build the form field.
    # The parent class sets this on its field_type; redefining the field
    # creates a new object without the attribute, so re-apply it here.
    field_type.required_on_save = True

    # Additional column for the reCAPTCHA v3 score threshold. Nullable, so
    # hosts that only use the Turnstile type carry an unused column at most.
    recaptcha_score_threshold = models.FloatField(
        null=True,
        blank=True,
        default=0.5,
        verbose_name="reCAPTCHA v3 Score Threshold",
        help_text=(
            "Score threshold for reCAPTCHA v3 (0.0 to 1.0). Only applies to "
            "reCAPTCHA v3 fields. Default: 0.5"
        ),
    )

    panels = [
        FieldPanel("field_type", classname="formbuilder-type"),
        FieldPanel(
            "label",
            classname="formbuilder-label",
            help_text=LABEL_HELP_TEXT,
        ),
        FieldPanel("help_text", classname="formbuilder-help_text"),
        FieldPanel("required", classname="formbuilder-required"),
        FieldPanel("choices", classname="formbuilder-choices"),
        FieldPanel(
            "recaptcha_score_threshold",
            classname="formbuilder-recaptcha-threshold",
        ),
    ]

    class Meta:
        abstract = True
