from django.core.mail.backends.smtp import EmailBackend as SmtpEmailBackend
from django.core.mail.backends.console import EmailBackend as ConsoleEmailBackend
from django.conf import settings

class DatabaseEmailBackend:
    """
    Dynamic Django Email Backend that reads SMTP configuration from the database (EmailSettings).
    Falls back gracefully to settings.DEFAULT_FALLBACK_EMAIL_BACKEND or ConsoleEmailBackend if not configured or disabled.
    """
    def __init__(self, fail_silently=False, **kwargs):
        self.fail_silently = fail_silently
        self.backend = None
        self._init_backend()

    def _init_backend(self):
        try:
            from website.models import EmailSettings
            smtp_cfg = EmailSettings.load()
            if smtp_cfg and smtp_cfg.is_enabled and smtp_cfg.smtp_host:
                use_tls = (smtp_cfg.security == 'TLS')
                use_ssl = (smtp_cfg.security == 'SSL')
                raw_password = smtp_cfg.get_password()
                self.backend = SmtpEmailBackend(
                    host=smtp_cfg.smtp_host,
                    port=smtp_cfg.smtp_port,
                    username=smtp_cfg.smtp_username,
                    password=raw_password,
                    use_tls=use_tls,
                    use_ssl=use_ssl,
                    timeout=10,
                    fail_silently=self.fail_silently,
                )
                return
        except Exception:
            pass

        # Fallback to standard console or environment configured backend
        fallback_cls = getattr(settings, 'CONSOLE_EMAIL_FALLBACK', ConsoleEmailBackend)
        self.backend = fallback_cls(fail_silently=self.fail_silently)

    def open(self):
        return self.backend.open()

    def close(self):
        return self.backend.close()

    def send_messages(self, email_messages):
        self._init_backend()
        return self.backend.send_messages(email_messages)

