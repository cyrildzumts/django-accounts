from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import auth, messages
from django.utils.translation import gettext as _
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from accounts import constants as Account_Constants, account_services
from accounts.models import Account
from accounts.forms import  AccountCreationForm, UserSignUpForm, UpdateAccountForm
from accounts.account_services import AccountService
from accounts.resources import ui_strings
from django.conf import settings
import logging

logger = logging.getLogger('accounts')

# Create your views here.
def login(request):
    """
    Log in view
    """
    page_title = _("Login")
    template_name = 'accounts/registration/login.html'
    context = {}
    if request.method == 'POST':
        next_url = request.POST.get('next', '/')
        result = AccountService.process_login_request(request)
        if result['user_logged']:
            user = result['user']
            logger.info(f"User {user.username} logged in")
            return redirect(next_url)
        else:
            context['login_error'] = result['login_error']
    
    form = AccountService.get_authentication_form()
    register_form = AccountService.get_registration_form()
    next_url = request.GET.get('next', '/')
    context.update({
        
        'page_title':page_title,
        'template_name':template_name,
        'next_url': next_url,
        'form': form,
        'registration_form': register_form,
    })
    return render(request, template_name, context)


def logout(request):
    """
    Log out view
    """
    auth.logout(request)
    return redirect('home')


def register(request):
    """
    User registration view
    """
    template_name = "registration/register.html"
    page_title = _('Registration')
    logger.info("New registration request")
    if request.method == 'POST':
        result = AccountService.process_registration_request(request)
        if result['user_created']:
            messages.add_message(request, messages.SUCCESS, ui_strings.ACCOUNT_REGISTRATION_SUCCESS_MESSAGE)
            return redirect("accounts:registration-complete")
        else:
            messages.add_message(request, messages.ERROR, ui_strings.ACCOUNT_REGISTRATION_ERROR_MESSAGE)
            account_form = AccountCreationForm(request.POST)
            user_form = UserSignUpForm(request.POST)

    else:
        # form = UserCreationForm()
        #form = AccountService.get_registration_form()
        account_form = AccountCreationForm()
        user_form = UserSignUpForm()
    context = {
        'page_title': page_title,
        'template_name': template_name,
        #'form': form,
        'account_form' : account_form,
        'user_form': user_form,
        'ACCOUNT_TYPE': Account_Constants.ACCOUNT_TYPE
    }
    return render(request, template_name, context)

def send_validation(request, account_uuid):
    account = get_object_or_404(Account, account_uuid=account_uuid)
    email_sent = False
    queryset = Account.objects.filter(account_uuid=account_uuid, email_validated=True)
    if not queryset.exists():
        logger.debug(f" account {account} not validated. sending validation link now")
        token = AccountService.generate_email_validation_token()
        expiration_date = AccountService.get_token_expire_time()
        account.email_validation_token = token
        account.validation_token_expire = expiration_date
        account.save()
        #queryset.update(email_validation_token=token, validation_token_expire=expiration_date)
        #account.refresh_from_db()
        email_context = {
            'template_name': settings.DJANGO_VALIDATION_EMAIL_TEMPLATE,
            'title': 'Validation de votre adresse mail',
            'recipient_email': account.user.email,
            'context':{
                'SITE_NAME': settings.SITE_NAME,
                'SITE_HOST': settings.SITE_HOST,
                'FULL_NAME': account.user.get_full_name(),
                'validation_url' : settings.SITE_HOST + account.get_validation_url()
            }
        }
        account_services.send_validation_mail(email_context)
        email_sent = True
        
    if email_sent:
        messages.add_message(request, messages.INFO, "Validation has been sent")
        logger.debug(f" account {account} not validated. Validation link sent")
    else:
        messages.add_message(request, messages.WARNING, "Validation could not be sent")
        logger.warn(f" account {account} not validated. Validation link not sent")

    return redirect('home')

def validation_sent(request, info=None):
    if info:
        account = info.get('account', None)
        
    pass

def email_validation(request, account_uuid=None, token=None):

    template_name = "registration/email_validation.html"
    page_title = "Email Validation"
    account = get_object_or_404(Account, account_uuid=account_uuid, email_validation_token=token)
    result = AccountService.validate_email(account_uuid=account_uuid, token=token)
    context = {
        'account'   : account,
        'validated' : result['validated'],
        'msg'       : result['message'],
        'page_title': page_title
    }
    return render(request, template_name, context)


@login_required
def password_change_views(request):
    """ 
        This view is called when the user want to change its password
    """
    page_title = _('Password Modification')
    template_name = "registration/password_change.html"
    success_url = 'accounts:password-change-done'
    if request.method == 'POST':
        postdata = request.POST.copy()
        form = PasswordChangeForm(request.user, postdata)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, ui_strings.USER_PASSWORD_CHANGED_SUCCESS)
            context = {
                'changed' : True,
                'redirect_to': success_url
            }
            return redirect(success_url)
        else:
            messages.error(request, ui_strings.ACCOUNT_INVALID_FORM_DATA)
    else:
        form = PasswordChangeForm(request.user)
    
    context = {
        'page_title': page_title,
        'form' : form
    }
    return render(request, template_name, context)
    

def password_change_done_views(request):
    """ 
        This view is called when the user has changed its password
    """
    template_name = "registration/password_change_done.html"
    page_title = _('Confirmation')
    
    context = {
        'page_title': page_title,
        'template_name': template_name
    }
    return render(request, template_name, context)



def registration_complete(request):
    """ 
        This view is called when the user has changed its password
    """
    template_name = "registration/registration_complete.html"
    page_title = _('Registration Confirmation')
    context = {
        'page_title': page_title,
        'template_name': template_name
    }
    return render(request, template_name, context)


def password_reset_views(request):
    """ 
        This view is called when the user want to reset her password
    """
    template_name = "registration/password_reset_form.html"
    email_template_name = "registration/password_reset_email.html"
    page_title = _('Password reinitialization')

    
    context = {
        'page_title': page_title,
        'template_name': template_name
    }
    return render(request, template_name, context)

@login_required
def user_account(request):
    """
     This method serves the default user account page.
     This page display an overview of the user's orders,
     user's infos ...  So this method have to provide these
     informations to the template.
     This view must provide a context providing the following informations :
     *current balance
     *transaction history
     *list of available services
     *a list of favoris
    """
    template_name = "accounts/account.html"
    page_title = _('My Account')
    name = request.user.get_full_name()
    current_account = get_object_or_404(Account, user=request.user)
    context = {
        'name'          : name,
        'page_title'    : page_title,
        'account'       : current_account
    }
    
    return render(request, template_name, context)

@login_required
def account_details(request, account_uuid=None):
    page_title = _("Account Details")
    instance = get_object_or_404(Account, account_uuid=account_uuid)
    template_name = "accounts/account_detail.html"
    #form = AccountForm(request.POST or None, instance=instance)
    context = {
        'page_title':page_title,
        'template_name':template_name,
        'account': instance
    }
    return render(request,template_name,context )


@login_required
def account_update(request, account_uuid=None):
    
    page_title = _("Edit my account")
    instance = get_object_or_404(Account, account_uuid=account_uuid)
    template_name = "accounts/account_update.html"
    if request.method =="POST":
        form = UpdateAccountForm(request.POST, instance=instance)
        if form.is_valid():
            logger.info("Edit Account form is valid. newsletter : %s", form.cleaned_data['newsletter'])
            form.save()
            messages.success(request, ui_strings.ACCOUNT_UPDATE_SUCCESS_MESSAGE)
            return redirect('accounts:account')
        else:
            logger.info("Edit Account form is not valid. Errors : %s", form.errors)
            messages.warning(request, ui_strings.ACCOUNT_UPDATE_ERROR_MESSAGE)
    else :
        form = UpdateAccountForm(instance=instance)
    context = {
            'page_title':page_title,
            'template_name':template_name,
            'account' : instance,
            'balance'     : instance.balance,
            'form': form
        }
    return render(request, template_name,context )



