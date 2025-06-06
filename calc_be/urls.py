from .views import AnalyzeImageView
from django.urls import path
from . import views

urlpatterns = [
    path('calculate/analyze/', AnalyzeImageView.as_view(), name='analyze-image'),
    path('', views.login_register, name='auth_home'),       # for the form UI
    path('login/', views.login_view, name='do_login'),       # for POST login
    path('register/', views.register, name='register'),
    path('forgot/', views.forgot_password, name='forgot_password'),
    path('verify/', views.verify_otp, name='verify_otp'),
    path('reset/', views.reset_password, name='reset_password'),
    path('social/', views.social_redirect, name='social'),
    path('debug/socialapps/',views.debug_socialapps ),
]