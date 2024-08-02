from django.db import models
from django.utils import timezone


class Secret(models.Model):
    class Meta:
        ordering = ['pk']

    text = models.CharField(max_length=300, blank=False, null=False)
    passphrase = models.CharField(max_length=100, blank=False, null=False)
    secret_key = models.CharField(max_length=300, blank=False, null=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    expires_at = models.DateTimeField(null=True)  # дата истечения времени жизни

    def has_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self) -> str:
        return f"Secret({self.pk})"
