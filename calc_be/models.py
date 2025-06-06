from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class OTPModel(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)  

    def is_expired(self):
        return timezone.now() > self.created_at + timezone.timedelta(minutes=3) 

class LoginAttempt(models.Model):
    username = models.CharField(max_length=150, unique=True)
    attempts = models.IntegerField(default=0)
    last_attempt = models.DateTimeField(auto_now=True)

    def is_locked(self):
        if self.attempts < 3:
            return False
        elapsed = timezone.now() - self.last_attempt
        return elapsed.total_seconds() < 180  # 3 minutes

    def get_cooldown_remaining(self):
        elapsed = timezone.now() - self.last_attempt
        return int(180 - elapsed.total_seconds())

    def increment(self):
        self.attempts += 1
        self.save()

    def reset(self):
        self.attempts = 0
        self.save()

    def __str__(self):
        return f"{self.username} - {self.attempts} attempts"
