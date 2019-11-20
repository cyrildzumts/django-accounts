from django.contrib import auth
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as django_login, logout as django_logout
from django.contrib.auth.forms import PasswordChangeForm
from django.db import IntegrityError
from abc import ABCMeta, ABC
from accounts.forms import  RegistrationForm, AuthenticationForm, AccountForm, UserSignUpForm, AccountCreationForm
from accounts.models import Account
from django.db.models import F, Q
from django.apps import apps
from django.forms import modelform_factory
import sys
import logging
import numbers
import uuid

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
        result_dict['next_url'] = "/"
        postdata = request.POST.copy()
        form = AuthenticationForm(data=postdata)
        username = postdata['username']
        password = postdata['password']
        logger.info("[AccountService.process_login_request] : starting")
        if form.is_valid():
            logger.debug("[AccountService.process_login_request] : form is valid Username : {} - Password : {}".format(username,password))
            user = auth.authenticate(username=username,
                                    password=password)
            logger.debug("[AccountService.process_login_request] : user authentication")
            if user is not None:
                if user.is_active:
                    auth.login(request, user)
                    logger.debug("[AccountService.process_login_request] : user is authenticated")
                    result_dict['user_logged'] = True
                
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
        account_form = AccountCreationForm(postdata)
        user_form_is_valid = user_form.is_valid()
        account_form_is_valid = account_form.is_valid()
        if user_form_is_valid and account_form_is_valid:
            logger.info("User creation data is valid")
            user = user_form.save()
            result_dict['user_created'] = True
            logger.info('User {} has been created', user.username)
            user.refresh_from_db()
            account_form = AccountCreationForm(postdata, instance=user.account)
            account_form.full_clean()
            account_form.save()
            result_dict['account_created'] = True
            logger.debug("User Account creation succesfull")
                
        else :
            logger.error("Error on registration below is the errors found in the submitted form : ")
            if not user_form_is_valid:
                logger.error( "User form data invalid: %s",user_form.errors)
            if not account_form_is_valid:
                logger.error( "Account form data invalid: %s",account_form.errors)
        return result_dict


    @staticmethod
    def generate_email_validation_token(account_uuid=None):
        token = uuid.uuid4()
        validated = 1 == Account.objects.filter(account_uuid=account_uuid).update(email_activation_tocken=token)
        return token, validated
    @staticmethod
    def validate_email(account_uuid, token):
        validated = False
        account = None
        if account_uuid and token:
            account = AccountService.get_account(account_uuid)
            if account and token and account.email_validation_token == token :
                updated = Account.objects.filter(pk=account.pk, email_validation_token=token).update(email_validated=True, email_validated_token=None)
                validated = updated == 1
        return account, validated

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


    
