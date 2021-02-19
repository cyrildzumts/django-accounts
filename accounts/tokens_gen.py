from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils import six, timezone
from accounts import constants
import secrets
import datetime

class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
            six.text_type(user.pk) + six.text_type(timestamp) +
            six.text_type(user.profile.email_confirmed)
        )

account_activation_token = AccountActivationTokenGenerator()

def get_activation_token():
    return secrets.token_urlsafe(constants.TOKEN_LENGTH)

