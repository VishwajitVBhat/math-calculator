from django.contrib import admin
from .models import OTPModel, LoginAttempt

admin.site.register(OTPModel)
admin.site.register(LoginAttempt)