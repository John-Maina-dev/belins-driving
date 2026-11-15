import time
from datetime import datetime, date
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import UserProfile
from students.validators import validate_age_18_plus
from courses.models import Branch
from website.models import SiteSettings


def _get_max_dob_str():
    today = timezone.localdate() if hasattr(timezone, 'localdate') else date.today()
    try:
        max_date = today.replace(year=today.year - 18)
    except ValueError:
        max_date = today.replace(year=today.year - 18, day=28)
    return max_date.strftime('%Y-%m-%d')


def login_view(request):
    """
    Public and staff authentication entry point.
    Redirects authorized managers to /manage/ and students to /students/dashboard/.
    Enforces clear user-friendly error messages for PENDING and REJECTED accounts.
    """
    if request.user.is_authenticated:
        if request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.is_management_authorized):
            return redirect('manage:dashboard')
        return redirect('students:dashboard')

    if request.GET.get('timeout') == '1':
        storage = messages.get_messages(request)
        existing = [str(m) for m in storage]
        storage.used = False
        if not any("inactivity" in m.lower() for m in existing):
            messages.warning(request, "You were logged out due to inactivity.")

    next_url = request.GET.get('next', '')

    if request.method == 'POST':
        identifier = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        # Allow logging in with either username or email
        if '@' in identifier:
            user_obj = User.objects.filter(email__iexact=identifier).first()
            if user_obj:
                identifier = user_obj.username

        user = authenticate(request, username=identifier, password=password)

        if user is not None:
            login(request, user)
            request.session['last_activity_ts'] = time.time()
            # Keep underlying session cookie alive for 7 days; InactivityTimeoutMiddleware
            # enforces session_timeout_minutes and redirects cleanly to /login/?timeout=1
            request.session.set_expiry(60 * 60 * 24 * 7)

            if next_url and next_url.startswith('/'):
                if next_url.startswith('/manage/') and not (user.is_superuser or (hasattr(user, 'profile') and user.profile.is_management_authorized)):
                    messages.info(request, "Welcome! You have been directed to your student dashboard.")
                    resp = redirect('students:dashboard')
                else:
                    resp = redirect(next_url)
            elif user.is_superuser or (hasattr(user, 'profile') and user.profile.is_management_authorized):
                resp = redirect('manage:dashboard')
            else:
                resp = redirect('students:dashboard')
            resp.delete_cookie('explicit_logout')
            return resp
        else:
            auth_error = getattr(request, 'auth_error', None)
            if auth_error:
                messages.error(request, auth_error)
            else:
                messages.error(request, "Invalid username/email or password. Please try again.")

    return render(request, 'accounts/login.html', {'next': next_url})


def logout_view(request):
    """Log out user (POST form) and redirect to login or homepage."""
    logout(request)
    messages.info(request, "You have been logged out.")
    resp = redirect('website:home')
    resp.set_cookie('explicit_logout', '1', max_age=86400, httponly=True, samesite='Lax')
    return resp


def keep_alive_view(request):
    """AJAX keep-alive endpoint to extend active user session."""
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'expired', 'message': 'You were logged out due to inactivity.'}, status=401)
    request.session['last_activity_ts'] = time.time()
    try:
        s_obj = SiteSettings.load()
        t_mins = s_obj.session_timeout_minutes if s_obj and s_obj.session_timeout_minutes else 15
    except Exception:
        t_mins = 15
    timeout_seconds = max(60, int(t_mins) * 60)
    request.session.set_expiry(60 * 60 * 24 * 7)
    request.session.modified = True
    return JsonResponse({'status': 'ok', 'timeout_seconds': timeout_seconds})


def register_view(request):
    """
    Public user account registration.
    Requires Date of Birth and enforces Age 18+.
    New accounts are assigned PENDING approval status and blocked from login
    until the Super Admin reviews and approves them.
    """
    if request.user.is_authenticated:
        return redirect('website:home')

    branches = Branch.objects.filter(is_active=True).order_by('order', 'name')
    context = {
        'branches': branches,
        'max_dob': _get_max_dob_str(),
    }

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        dob_str = request.POST.get('date_of_birth', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        context['form_data'] = request.POST

        if not first_name or not last_name or not email or not password or not dob_str:
            messages.error(request, "Please fill in all required fields, including Date of Birth.")
            return render(request, 'accounts/register.html', context)

        try:
            dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
            validate_age_18_plus(dob)
        except ValueError:
            messages.error(request, "Enter a valid Date of Birth in YYYY-MM-DD format.")
            return render(request, 'accounts/register.html', context)
        except ValidationError as e:
            messages.error(request, e.messages[0] if hasattr(e, 'messages') else str(e))
            return render(request, 'accounts/register.html', context)

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'accounts/register.html', context)

        if len(password) < 6:
            messages.error(request, "Password must be at least 6 characters long.")
            return render(request, 'accounts/register.html', context)

        if User.objects.filter(email__iexact=email).exists():
            messages.error(request, "An account with this email address already exists. Please log in.")
            return render(request, 'accounts/register.html', context)

        base_username = email.split('@')[0]
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        profile = user.profile
        profile.role = UserProfile.ROLE_STUDENT
        profile.approval_status = UserProfile.APPROVAL_PENDING
        profile.phone = phone
        profile.date_of_birth = dob
        profile.save()

        messages.success(
            request,
            "Your registration was received. You can log in once the school approves your account."
        )
        return redirect('accounts:login')

    return render(request, 'accounts/register.html', context)
