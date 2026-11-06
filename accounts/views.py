from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from .forms import UserRegistrationForm, UserLoginForm, UserProfileUpdateForm
from .models import UserProfile
from recommendations.models import MoodHistory
from watchlist.models import Watchlist

def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Ensure profile exists
            UserProfile.objects.get_or_create(user=user)
            login(request, user)
            messages.success(request, f"Welcome to MoodFlix, {user.username}! Your mood journey begins now.")
            return redirect('home')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    next_url = request.GET.get('next', 'home')

    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect(request.POST.get('next') or 'home')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = UserLoginForm()

    return render(request, 'accounts/login.html', {'form': form, 'next': next_url})


def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
        messages.info(request, "You have been logged out. See you next time!")
    return redirect('home')


@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    recent_moods = MoodHistory.objects.filter(user=request.user).order_by('-selected_at')[:10]
    
    total_saved = Watchlist.objects.filter(user=request.user).count()
    watched_count = Watchlist.objects.filter(user=request.user, watched=True).count()
    unwatched_count = total_saved - watched_count

    context = {
        'profile': profile,
        'recent_moods': recent_moods,
        'total_saved': total_saved,
        'watched_count': watched_count,
        'unwatched_count': unwatched_count,
        'preferred_moods_list': profile.get_preferred_moods_list(),
    }
    return render(request, 'accounts/profile.html', context)


@login_required
@require_http_methods(['GET', 'POST'])
def profile_update_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST, instance=profile, user=request.user)
        if form.is_valid():
            # Update User model fields
            request.user.first_name = form.cleaned_data['first_name']
            request.user.last_name = form.cleaned_data['last_name']
            request.user.email = form.cleaned_data['email']
            request.user.save()

            # Update Profile model fields
            profile = form.save(commit=False)
            selected_moods = form.cleaned_data.get('preferred_moods_select', [])
            profile.preferred_moods = ','.join(selected_moods)
            profile.save()

            messages.success(request, "Your profile and preferences have been updated successfully.")
            return redirect('accounts:profile')
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = UserProfileUpdateForm(instance=profile, user=request.user)

    return render(request, 'accounts/profile_edit.html', {'form': form, 'profile': profile})
