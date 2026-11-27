from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class EmailOrUsernameBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or password is None:
            return None
        User = get_user_model()
        matches = list(User.objects.filter(username__iexact=username).order_by('pk')[:2])
        if len(matches) > 1:
            matches = [item for item in matches if item.username == username]
        if not matches and '@' in username:
            matches = list(User.objects.filter(email__iexact=username)[:2])
        if len(matches) != 1:
            User().set_password(password)
            return None
        user = matches[0]
        return user if user.check_password(password) and self.user_can_authenticate(user) else None
