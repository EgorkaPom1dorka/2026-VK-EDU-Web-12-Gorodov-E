from django.contrib.auth import authenticate, login, logout
from .forms import LoginForm, SignupForm
from django.contrib.auth.models import User
from core.models import Profile
from .forms import ProfileForm
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserEditForm, ProfileEditForm

def logout_view(request):
    logout(request)
    return redirect('index')

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            if user:
                login(request, user)
                return redirect('index')
    else:
        form = LoginForm()
    return render(request, 'core/login.html', {'form': form})

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            Profile.objects.create(user=user)
            login(request, user)
            return redirect('index')
    else:
        form = SignupForm()
    return render(request, 'core/signup.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('index')

@login_required(login_url='/login/')
def profile(request):
    user_profile = getattr(request.user, 'profile', None)

    if request.method == 'POST':
        user_form = UserEditForm(request.POST, instance=request.user)
        profile_form = ProfileEditForm(request.POST, request.FILES, instance=user_profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Изменения успешно сохранены!')
            return redirect('profile')
    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=user_profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    return render(request, 'core/profile.html', context)