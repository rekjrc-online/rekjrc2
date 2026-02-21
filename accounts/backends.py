from django.contrib.auth import get_user_model


class EmailBackend:
    """
    Authenticate against email address instead of username.
    Email lookup is case-insensitive — the input is lowercased before querying
    so 'User@Example.com' and 'user@example.com' resolve to the same account.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            return None

        User = get_user_model()
        email = username.lower().strip()

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return None

        if user.check_password(password):
            return user

        return None

    def get_user(self, user_id):
        User = get_user_model()
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None