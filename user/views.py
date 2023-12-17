from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import redirect, render

from .forms import LoginForm, RegisterForm


# Create your views here.
def register(request):

    form = RegisterForm(request.POST or None)

    if form.is_valid():
        username = str(form.cleaned_data.get("username"))
        mail = form.cleaned_data.get("mailadress")
        password = form.cleaned_data.get("password")

        newUser = User(username = username)
        newUser.email = mail
        newUser.set_password(password)

        newUser.save()
        login(request, newUser)
        messages.success(request, "Registered Successfully")

        return redirect("index")
        
    context = {
            "form":form
        }
    return render(request, "register.html", context)

def loginUser(request):
    form = LoginForm(request.POST or None)
    context = {
        "form":form
    }

    if form.is_valid():
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password")

        user = authenticate(username=username, password=password)

        if user is None:
            messages.info(request, "Email or Password is Incorrect")
            return render(request, "login.html", context)
        
        messages.success(request, "You have successfully logged in")
        login(request, user)
        return redirect("index")
    return render(request, "login.html", context)

def logoutUser(request):
    logout(request)
    messages.success(request, "You have successfully logged out")
    return redirect('index')