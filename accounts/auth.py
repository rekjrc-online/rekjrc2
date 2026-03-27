from mozilla_django_oidc.auth import OIDCAuthenticationBackend

class CustomOIDCBackend(OIDCAuthenticationBackend):
    def create_user(self, claims):
        email = claims.get('email', '').lower()
        if not email:
            return None
        return self.UserModel.objects.create_user(
            username=email,
            email=email,
            first_name=claims.get('given_name', ''),
            last_name=claims.get('family_name', ''),
            is_verified=True)

    def update_user(self, user, claims):
        user.first_name = claims.get('given_name', '')
        user.last_name = claims.get('family_name', '')
        user.save()
        return user