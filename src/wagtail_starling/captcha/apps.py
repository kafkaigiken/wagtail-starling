"""App config for wagtail_starling.captcha.

Registering this app in ``INSTALLED_APPS`` activates the admin JS hook —
the reCAPTCHA v3 score-threshold toggle ships as packaged app static, not
through a host build chain (hosts build assets differently; mix / vite / none).
"""

from django.apps import AppConfig


class CaptchaConfig(AppConfig):
    name = "wagtail_starling.captcha"
    label = "starling_captcha"
    verbose_name = "Wagtail Starling Captcha"

    def ready(self):
        from django.templatetags.static import static
        from django.utils.html import format_html
        from wagtail import hooks

        @hooks.register("insert_global_admin_js")
        def formfield_recaptcha_admin_js():
            """Toggle the v3 score-threshold field on captcha FormField rows."""
            return format_html(
                '<script src="{}" defer></script>',
                static("wagtail_starling/captcha/js/formfield_recaptcha.js"),
            )
