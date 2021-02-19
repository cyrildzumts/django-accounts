
from django.utils import timezone
from accounts import constants
import secrets
import datetime


def get_activation_token():
    return secrets.token_urlsafe(constants.TOKEN_LENGTH)

