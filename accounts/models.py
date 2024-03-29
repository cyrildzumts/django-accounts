from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone
from django.utils import crypto
from accounts import constants as ACCOUNT_CONSTANTS
import uuid
import secrets
import datetime

def get_activation_token():
    return secrets.token_urlsafe(ACCOUNT_CONSTANTS.TOKEN_LENGTH)

def ident_file_path(instance, filename):
    file_ext = filename.split(".")[-1]
    name = "avatar" + "." + file_ext
    return "identifications/ser_{0}_{1}".format(instance.user.id, name)

def generate_customer_id():
    return crypto.get_random_string(length=9, allowed_chars=ACCOUNT_CONSTANTS.RANDOM_CUSTOMER_ID_CHARACTERS)

class Account(models.Model):
    """
    The Account Model extends the User Model with a profile.
    This model provides extra information to identify a user.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to=ident_file_path,null=True, blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    telefon = models.CharField(default='', max_length=15, null=True, blank=True)
    newsletter = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    customer_id = models.IntegerField(default=generate_customer_id, blank=True, null=True)
    account_type = models.IntegerField(default=ACCOUNT_CONSTANTS.ACCOUNT_PRIVATE, blank=True, null=True, choices=ACCOUNT_CONSTANTS.ACCOUNT_TYPE)
    account_uuid = models.UUIDField(default=uuid.uuid4, editable=False, blank=True, null=True)
    email_validation_token = models.CharField(max_length=128, default=get_activation_token, blank=True, null=True)
    validation_token_expire = models.DateTimeField(blank=True, null=True)
    email_validated = models.BooleanField(default=False, blank=True, null=True)
    is_active = models.BooleanField(default=False, blank=True, null=True)
    created_by = models.ForeignKey(User, related_name="created_accounts", null=True,blank=True, on_delete=models.SET_NULL)
    reset_token = models.CharField(max_length=8,blank=True, null=True)


    class Meta:
        permissions = (
            ('api_add_account', "Can add  an account through rest api"),
            ('api_view_account', 'Can read through a rest api'),
            ('api_change_account', 'Can edit through a rest api'),
            ('api_delete_account', 'Can delete through a rest api'),
            ('api_recharge_customer_account', 'can recharge customer account through api'),

        )

    def __str__(self):
        return self.user.get_full_name()


    def get_absolute_url(self):
        return reverse('accounts:account-detail', kwargs={'account_uuid':self.account_uuid})
    
    def get_validation_url(self):
        return reverse('accounts:email-validation', kwargs={'account_uuid':self.account_uuid, 'token': self.email_validation_token})

    def full_name(self):
        return self.user.get_full_name()
    
    def initial(self):
        return ''.join(i[0] for i in self.user.get_full_name().split()).upper()




    


@receiver(post_save, sender=User)
def create_or_update_account(sender,instance, created,  **kwargs):
    """
    This slot is called whenever a new User is created.
    There are two way to create a new user : From the Admin Site and 
    from A views. When a new User is created from the Admin Site, an account 
    profile is also created, so we don't have create an associated account again when
    this slot is executed.
    When a new User created from a views or programmatically, there is no associated account 
    to the new user, so we have to create a new account for that user.
    """
    if created:
        # first check if instance already has a account profile
        # if the user hasn't an associated account profile then we create an Profile account.
        #
        if not Account.objects.filter(user=instance).exists():
            Account.objects.create(user=instance, validation_token_expire=timezone.now() + datetime.timedelta(hours=ACCOUNT_CONSTANTS.ACTIVATION_DELAY_HOURS))
            print("Account instance created")
    return
        

