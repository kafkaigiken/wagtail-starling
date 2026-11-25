"""wagtail_starling.captcha — captcha field types for the Wagtail form builder.

A canonical, once-implemented set of bot-gate FormField types that consumer
projects (medan, male, …) compose with their own ``FormField``/``FormPage``
models. Extracted from two independent consumer implementations whose copies
had already drifted (settings names, backends, dev behavior).

Install as its own app — it is inert unless listed in ``INSTALLED_APPS``::

    INSTALLED_APPS = [..., "wagtail_starling.captcha"]

Dependencies ride as extras — install with ``wagtail-starling[captcha]``
when using the reCAPTCHA field types; Turnstile-only consumers need no extra
(the recaptcha imports are deferred to the ``create_recaptcha_*`` methods).

Behavior contract (every adopter can test against this):

- **Closed never open.** An unreachable verification endpoint fails the form;
  a missing/rejected token fails the form whenever a real secret is set.
- **Real secret ⇒ gate mandatory.** Turnstile's ``required`` flag is decided
  by the configured secret, not by the admin row's checkbox (Wagtail defaults
  the checkbox to True, which would have defeated the dev downgrade).
- **Cloudflare test secret ⇒ token optional.** The documented test secrets
  (always-pass set) mark a dev checkout; a missing token must not block
  local form testing there.
- **No kill switch.** There is no env flag that removes both the widget and
  validation (the third-party field male ran had one: ``TURNSTILE_ENABLE=0``
  rendered nothing *and* skipped verification — a fully open gate).
- **Single settings name per key.** ``TURNSTILE_SITE_KEY`` /
  ``TURNSTILE_SECRET_KEY`` (+ ``RECAPTCHA_PUBLIC_KEY`` / ``RECAPTCHA_PRIVATE_KEY``
  / ``RECAPTCHA_REQUIRED_SCORE`` for the reCAPTCHA types).
- **Host-owned models stay host-owned.** The mixin contributes choices, the
  score-threshold column and panels; the migrations remain in each host app.
"""
