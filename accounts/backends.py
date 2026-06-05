from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class EmailOrUsernameModelBackend(ModelBackend):
    """Allow existing users to sign in with either email or username."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(get_user_model().USERNAME_FIELD)

        if username is None or password is None:
            return None

        UserModel = get_user_model()
        login_value = username.strip()

        try:
            user = UserModel.objects.get(email__iexact=login_value)
        except UserModel.DoesNotExist:
            try:
                user = UserModel.objects.get(username__iexact=login_value)
            except UserModel.DoesNotExist:
                UserModel().set_password(password)
                return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None
