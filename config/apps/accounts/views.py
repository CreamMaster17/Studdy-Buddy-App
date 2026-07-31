from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from .models import UserProfile

User = get_user_model()

def test_insert(request):
    try:
        User.objects.all().delete()

        User.objects.create_user(
            username="Bruhdy",
            email="Bruhdy@email.com",
            password=("letmeinplease")
        )

        User.objects.create_user(
            username="Donny",
            email="Donny@email.com",
            password=("Passingword")
        )

        message = "Database Creation Successful"

    except Exception as e:
        message =f"Error Making Database: {e}"

    return render(request, "Test_Insert.html",{"display_message": message})


def login_page(request):

    if request.method == "POST":
        username_input = request.POST.get("username")
        password_input = request.POST.get("password")

        user = authenticate(request, username=username_input, password=password_input)

        if user is not None:
            login(request, user)

            return redirect("studybuddy_cms:home")
        else:
            messages.error(request, f"Invalid username or password.")

    return render(request, "login.html")


def registration_page(request):

    if request.method == "POST":
        
        username_input = request.POST.get("username")
        email_input = request.POST.get("email")
        password_input = request.POST.get("password")

        try:
            User.objects.create_user(
                username=username_input,
                email=email_input,
                password=password_input
            )

            messages.success(request, "Account was successfully created!")

        except IntegrityError as e:
            messages.error(request, f"An account already exists with that username/email.")
        
    return render(request, "registration.html")

@login_required
def user_settings(request):

    profile = request.user.profile
    if request.method == "POST":
        request.user.username = request.POST.get("username") or request.user.username
        request.user.email = request.POST.get("email") or request.user.email
        profile.nickname = request.POST.get("nickname") or profile.nickname

        password = request.POST.get("password")
        if password:
            request.user.set_password(password)
            update_session_auth_hash(request, request.user)

        request.user.save()

        if request.FILES.get("profile_picture"):
            profile.profile_picture = request.FILES["profile_picture"]

        profile.save()

        return redirect("accounts:user-settings")


    return render(request, "user-settings.html")