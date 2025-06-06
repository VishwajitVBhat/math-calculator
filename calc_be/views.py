# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .utils import analyze_image
from PIL import Image
import base64
from django.db import models
from io import BytesIO
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
from django.http import JsonResponse
from django.contrib.sites.models import Site
from django.http import HttpResponseForbidden
from .models import OTPModel, LoginAttempt
from allauth.socialaccount.models import SocialApp
from allauth.socialaccount.providers import registry
import random, os, subprocess
class AnalyzeImageView(APIView):
    def post(self, request):
        try:
            image_str = request.data.get('image')
            dict_of_vars = request.data.get('dict_of_vars', {})

            image_data = base64.b64decode(image_str.split(",")[1])
            image = Image.open(BytesIO(image_data))

            responses = analyze_image(image, dict_of_vars=dict_of_vars)

            return Response({
                "message": "Image processed",
                "data": responses,
                "status": "success"
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "message": f"Error: {str(e)}",
                "status": "error"
            }, status=status.HTTP_400_BAD_REQUEST)
# Custom user model extension (add to models.py)
def generate_otp():
    return str(random.randint(100000, 999999))

def debug_socialapps(request):
    apps = SocialApp.objects.all()
    return JsonResponse([
        {
            "provider": app.provider,
            "sites": [s.domain for s in app.sites.all()]
        }
        for app in apps
    ], safe=False)

# Render login/register form
def login_register(request):
    current_site = Site.objects.get_current()
    apps = SocialApp.objects.filter(sites=current_site)
    provider_ids = [app.provider for app in apps]
    return render(request, 'login/index.html', {'providers': provider_ids})

# User registration
def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return redirect('auth_home')

        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()
        messages.success(request, 'Registered successfully. Please log in.')
        return redirect('auth_home')
    return redirect('auth_home')

# Login logic with attempt limit
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        attempt, _ = LoginAttempt.objects.get_or_create(username=username)

        if attempt.is_locked():
            messages.error(request, f"Too many failed attempts. Try again in {attempt.get_cooldown_remaining()} seconds.")
            return redirect('auth_home')

        if user:
            auth_login(request, user)
            attempt.reset()
            try:
                vite_path = os.path.join("frontend", "calc-fe")
                if not os.path.exists(vite_path):
                    raise FileNotFoundError(f"Vite directory not found: {vite_path}")
                vite_server = subprocess.Popen(
                    [r"C:\Program Files\nodejs\npm.cmd", "run", "dev"],
                    cwd=vite_path
                )
            except FileNotFoundError as e:
                print(f"File not found: {e}")
            return redirect('http://localhost:5173')
        else:
            attempt.increment()
            messages.error(request, 'Invalid credentials')
            return redirect('auth_home')
    return redirect('auth_home')

# Forgot password - send OTP
def forgot_password(request):
    if request.method == 'POST':
        email = request.POST['email']
        users = User.objects.filter(email=email)
        if not users.exists():
            messages.error(request, 'Email not found')
            return redirect('forgot_password')
        user = users.first()
        otp = generate_otp()
        OTPModel.objects.update_or_create(user=user, defaults={'otp': otp})
        try:
            send_mail(
                'Your OTP Code',
                f'Your OTP is: {otp}',
                settings.DEFAULT_FROM_EMAIL,
                [email]
            )
            print(f"OTP sent to {email}: {otp}")
        except Exception as e:
            print("EMAIL ERROR:", e)
        request.session['reset_user'] = user.username
        return redirect('verify_otp')
    return render(request, 'login/forgot.html')


# OTP verification
def verify_otp(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        username = request.session.get('reset_user')
        if not username:
            messages.error(request, 'Session expired. Please try again.')
            return redirect('forgot_password')

        try:
            user = User.objects.get(username=username)
            otp_entry = OTPModel.objects.get(user=user)

            if otp_entry.is_expired():
                otp_entry.delete()  # Remove expired OTP
                messages.error(request, 'OTP expired. Please request a new one.')
                return redirect('forgot_password')

            if otp_entry.otp == entered_otp:
                otp_entry.delete()  # Optional: delete OTP after successful verification
                return redirect('reset_password')
            else:
                messages.error(request, 'Invalid OTP')
                return redirect('verify_otp')

        except OTPModel.DoesNotExist:
            messages.error(request, 'OTP not found. Please request a new one.')
            return redirect('forgot_password')
        except Exception as e:
            print("OTP verification error:", e)
            messages.error(request, 'Something went wrong')
            return redirect('forgot_password')

    return render(request, 'login/verify_otp.html')

# Password reset
def reset_password(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirm = request.POST['confirm_password']

        if password != confirm:
            messages.error(request, 'Passwords do not match')
            return redirect('reset_password')

        username = request.session.get('reset_user')
        user = User.objects.get(username=username)
        user.set_password(password)
        user.save()

        OTPModel.objects.filter(user=user).delete()
        messages.success(request, 'Password reset successful')
        return redirect('auth_home')
    return render(request, 'login/reset.html')

# Optional social redirect view
def social_redirect(request):
    return redirect('/')