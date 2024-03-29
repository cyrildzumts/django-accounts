from django.contrib import auth
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as django_login, logout as django_logout
from django.contrib.auth.forms import PasswordChangeForm
from django.db import IntegrityError
from abc import ABCMeta, ABC
from accounts.forms import  RegistrationForm, AuthenticationForm, AccountForm, UserSignUpForm, AccountCreationForm
from accounts.models import Account
from accounts import constants
from django.db.models import F, Q
from django.apps import apps
from django.forms import modelform_factory
from django.utils import timezone
from django.utils import crypto
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from accounts.resources import ui_strings
import sys
import logging
import numbers
import uuid
import secrets
import datetime

logger = logging.getLogger('accounts')


this = sys.modules[__name__]






def get_all_fields_from_form(instance):
    """"
    Return names of all available fields from given Form instance.

    :arg instance: Form instance
    :returns list of field names
    :rtype: list
    """

    fields = list(instance().base_fields)

    for field in list(instance().declared_fields):
        if field not in fields:
            fields.append(field)
    return fields

def print_form(form=None):
    print("Printing  Form Fields")
    if form :
        print(get_all_fields_from_form(form))
    else :
        print("form is not defined")




class AccountService(ABC):
    """
    This class exists only to avoid that the accounts.views directly manipulate the models it is working with.
    That way the Service can be changed without affecting the views.
    The job of this AccountService is to provide access to the database related to the Account operations.
    It provides differents utilities functions to obtains Forms, log user in, to create a new user account, 
    to create a new policy. 
    New bussiness services will be added to the class instead of updating the views.
    """

    @staticmethod
    def get_authentication_form(initial_content=False):
        return AuthenticationForm()
    
    @staticmethod
    def get_registration_form():
        return RegistrationForm()
    
    
    @staticmethod
    def get_account(account_uuid=None):
        account = None
        try:
            account = Account.objects.select_related('user').get(account_uuid=account_uuid)
        except Account.DoesNotExists:
            logger.error("No Account found with uuid %s", account_uuid)
        
        return account

    @staticmethod
    def process_change_password_request(request):
        result_dict = {}
        result_dict['changed'] = False
        
        postdata = request.POST.copy()
        form = PasswordChangeForm(request.user, postdata)
        if form.is_valid():
            user = form.save()
            result_dict['changed'] = True
            result_dict['next_url'] = 'accounts:password-change'
        return result_dict
        

    @staticmethod
    def process_login_request(request):
        result_dict = {}
        result_dict['user_logged'] = False
        postdata = request.POST.copy()
        form = AuthenticationForm(data=postdata)
        username = postdata.get('username', '')
        password = postdata.get('password')
        result_dict['username'] = username
        logger.info("[AccountService.process_login_request] : starting")
        if form.is_valid():
            logger.info("Login Form is valid")
            
            user = auth.authenticate(username=username, password=password)
            session_key = request.session.session_key
            if user is not None:
                logger.info(f"User {username} authenticated")
                if not user.account.email_validated and not user.is_superuser:
                    logger.info(f"User {username} email not validated")
                    result_dict['login_error'] = ui_strings.LOGIN_ACCOUNT_EMAIL_NON_VALIDATED_ERROR
                    
                    return result_dict
                if user.is_active:
                    logger.info(f"Trying to log User {username} in.")
                    session_items = request.session.items()
                    auth.login(request, user)
                    logger.debug(f"user {username} logged in")
                    result_dict['user_logged'] = True
                    result_dict['user'] = user
                    result_dict['next_url'] = request.GET.get('next', '/')
                    if hasattr(settings, 'SEND_USER_LOGGED_IN_SIGNAL') and settings.SEND_USER_LOGGED_IN_SIGNAL:
                        settings.SIGNA_USER_LOGGED_IN.send(sender=User, session_key=session_key, user=user,request=request, session_items=session_items)
                else:
                    result_dict['login_error'] = ui_strings.LOGIN_USER_INACTIVE_ERROR
            else:
                logger.warning(f"User {username} could not be found.")
                result_dict['login_error'] = ui_strings.ACCOUNT_INVALID_FORM_DATA
        else:
            result_dict['login_error'] = ui_strings.ACCOUNT_INVALID_FORM_DATA
            result_dict['form'] = form
        logger.debug("[AccountService.process_login_request] : finished")
        return result_dict
    

    @staticmethod
    def process_registration_request(request):
        """
        The form used to fill the data provide data for both the UserSignUpForm and the AccountCreationForm.
        From the data it is possible process many form at the same times just like this code is doing.
        """
        result_dict = {}
        result_dict['user_created'] = False
        result_dict['next_url'] = "/"
        postdata = request.POST.copy()
        user_form = UserSignUpForm(postdata)
        #account_form = AccountCreationForm(postdata)
        user_form_is_valid = user_form.is_valid()
        #account_form_is_valid = account_form.is_valid()
        if user_form_is_valid :
            session_key = request.session.session_key

            user = user_form.save()
            session_items = request.session.items()
            User.objects.filter(id=user.id).update(is_active=False)

            result_dict['user_created'] = True
            user.refresh_from_db()

            result_dict['user'] = user
            if hasattr(settings, 'SEND_USER_REGISTERED_SIGNAL') and settings.SEND_USER_REGISTERED_SIGNAL:
                        settings.SIGNA_USER_REGISTERED.send(sender=User, session_key=session_key, user=user,request=request, session_items=session_items)
            logger.info(f"New User {user.username} has been created")
                
        else :
            logger.error("Error on registration below is the errors found in the submitted form : ")
            result_dict['form'] = user_form
            if not user_form_is_valid:
                logger.error( f"User form data invalid: {user_form.errors}")

            #if not account_form_is_valid:
            #    logger.error( f"Account form data invalid: {account_form.errors}")
        return result_dict


    @staticmethod
    def generate_email_validation_token():
        token = secrets.token_urlsafe(constants.TOKEN_LENGTH)
        return token
    
    @staticmethod
    def get_token_expire_time():
        return timezone.now() +  datetime.timedelta(hours=constants.ACTIVATION_DELAY_HOURS)

    @staticmethod
    def validate_email(account_uuid, token):
        logger.info("validating email : ...")
        validated = False
        account = None
        msg = None
        now = timezone.now()
        if account_uuid and token:
            account = AccountService.get_account(account_uuid)
            logger.debug(f"Validating Account {account} - account token : {account.email_validation_token} -  submitted token : {token}")
            if account and token and account.email_validation_token == token :
                logger.debug(f"Account {account} token is valid. Now checking the expiration date has expired.")
                if account.validation_token_expire >= now :
                    validated = Account.objects.filter(pk=account.pk, email_validation_token=token).update(is_active=True,email_validated=True, email_validation_token=None) == 1
                    User.objects.filter(id=account.user.id).update(is_active=True)
                    msg = "Email validated"
                    logger.debug(f"Account {account} validated.")
                else:
                    msg = "Token has expired"
                    logger.warn(f"Account {account} not validated. {msg}  - now : {now} - expected expirationdate : {account.validation_token_expire}")
            else:
                msg = "Invalid data"
                logger.warn(f"Account {account} not validated. {msg}")
        else:
            msg = "Invalid data. Account or token missing"
            logger.warn(f"Account {account} not validated. {msg}")

        return {'account':account, 'validated' : validated, 'message' : msg}

    @staticmethod
    def create_account(accountdata=None, userdata=None):
        created = False
        if accountdata and userdata:
            try:
                user = User.objects.create(**userdata)
                user.refresh_from_db()
                # creating a new user will trigger a signal that will automatically create a new account the new user.
                # So instead of creating a new account , update the already created account associated to the new user.
                if user: 
                    Account.objects.filter(user=user).update(**accountdata)
                    created = True
            
            except IntegrityError:
                pass

        return created


def get_validation_url(account):
    if isinstance(account, Account):
        return account.get_validation_url()
    return None

def generate_customer_id():
    return crypto.get_random_string(length=9, allowed_chars=constants.RANDOM_CUSTOMER_ID_CHARACTERS)

def generate_customer_ids():
    queryset = Account.objects.all()
    for acc in queryset:
        acc.customer_id = generate_customer_id()
        acc.save()

    


def send_validation_mail(email_context):
    if email_context is not None and isinstance(email_context, dict):
        logger.debug("email_context available. Running send_mail now")
        try:
            template_name = email_context['template_name']
        except KeyError as e:
            logger.error(f"send_validation : template_name not available. Mail not send. email_context : {email_context}")
            return
        html_message = render_to_string(template_name, email_context['context'])
        send_mail(
            email_context['title'],
            None,
            settings.DEFAULT_FROM_EMAIL,
            [email_context['recipient_email']],
            html_message=html_message
        )
    else:
        logger.warn(f"send_validation: email_context missing or is not a dict. email_context : {email_context}")

    


    
