from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

UserModel = get_user_model()

class ApprovedUserBackend(ModelBackend):
    """
    Authentication backend enforcing account approval workflow.
    - Superusers always authenticate.
    - Regular users must have profile.approval_status == 'APPROVED'.
    - PENDING and REJECTED users are blocked from logging in across all interfaces
      (Django admin, standard login forms, API endpoints).
    """

    def user_can_authenticate(self, user):
        is_active = super().user_can_authenticate(user)
        if not is_active:
            return False
        if user.is_superuser:
            return True
        profile = getattr(user, 'profile', None)
        if not profile:
            return False
        return profile.approval_status == 'APPROVED'

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        if username is None or password is None:
            return None

        try:
            user = UserModel._default_manager.get_by_natural_key(username)
        except UserModel.DoesNotExist:
            UserModel().set_password(password)
            return None

        if user.check_password(password):
            if not user.is_active:
                if request:
                    setattr(request, 'auth_error', "This account is inactive. Please contact school administration.")
                return None
            if not user.is_superuser:
                profile = getattr(user, 'profile', None)
                if profile:
                    if profile.approval_status == 'PENDING':
                        msg = "Your registration was received. You can log in once the school approves your account."
                        if request:
                            setattr(request, 'auth_error', msg)
                        return None
                    elif profile.approval_status == 'REJECTED':
                        reason = profile.rejection_reason or "Account registration was not approved."
                        msg = f"Your account registration was rejected. Reason: {reason} Please contact administration if you believe this is an error."
                        if request:
                            setattr(request, 'auth_error', msg)
                        return None
            if self.user_can_authenticate(user):
                return user
        return None

