from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from .models import UserProfile

User = get_user_model()

@login_required
def home(request):
    
    return render(request, "home.html")

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

            print("LOGIN SUCCESSFUL")
            print("REDIRECTING TO HOME")

            return redirect("accounts:home")
        else:
            return render(request, "login.html", {"error": "Invalid username or password"})

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
            messages.error(request, f"An account already exists with that username.")
        
    return render(request, "registration.html")
