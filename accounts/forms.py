from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from accounts.models import Account
from django.contrib.admin.widgets import AdminDateWidget
from django.core.exceptions import ValidationError
from accounts import constants
import datetime

class UserForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name','password1', 'password2','email']
    
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Les mots de passe ne correspondent pas")
        
        return password1


    def save(self):
        user = super(UserForm, self).save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        user.set_password(self.cleaned_data['password1'])
        user.save()
        return user



class UpdateAccountForm(forms.ModelForm):
    
    class Meta:
        model = Account
        fields = ("telefon","newsletter",)


class UpdateUserForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ['first_name', 'last_name']


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['account_type','date_of_birth', 'telefon', 'newsletter']




# for the RegistrationForm , just allows user wo are at least
# 17 year old.
START = datetime.date(1960, 1, 1)
END = datetime.date.today().year - 16

YEARS_CHOICES = [y for y in range(START.year, END)]



class AuthenticationForm(forms.Form):
    """
    This is the Login Form.
    """
    username = forms.CharField(widget=forms.widgets.TextInput,
                               label="Nom d'utilisateur")
    password = forms.CharField(widget=forms.widgets.PasswordInput,
                               label='Mot de passse')

    class Meta:
        fields = ['username', 'password']
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        
        if username is None or len(username) < constants.USERNAME_MIN_LENGTH :
            raise ValidationError(f"invalid username: \"{username}\".  Username must be at least {constants.USERNAME_MIN_LENGTH} characters long")

        if not User.objects.filter(username=username).exists():
            raise ValidationError(f"bad username or password")
        return username



class UserSignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name','password1', 'password2','email']


    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if not first_name :
            raise ValidationError(f"missing first_name:")

        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if not last_name :
            raise ValidationError(f"missing last_name:")

        return last_name
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        
        if not username or len(username) < constants.USERNAME_MIN_LENGTH :
            raise ValidationError(f"invalid username: \"{username}\".  Username must be at least {constants.USERNAME_MIN_LENGTH} characters long")
        if User.objects.filter(username=username).exists():
            raise ValidationError(f"A user with this username : \"{username}\" is already in use")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email :
            raise ValidationError(f"missing email")
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already in use")
        return email


class AccountCreationForm(forms.ModelForm):

    class Meta:
        model = Account
        fields = ['account_type','date_of_birth', 'telefon', 'newsletter']
    




class RegistrationForm(forms.ModelForm):
    """
    Form for registering a new account.
    """
    username = forms.CharField(widget=forms.widgets.TextInput,
                               label="Nom d'utilisateur")
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)
    first_name = forms.CharField(widget=forms.widgets.TextInput,
                               label="Prénom")
    last_name = forms.CharField(widget=forms.widgets.TextInput,
                               label="Nom de famille")
    email = forms.CharField(widget=forms.widgets.TextInput,
                               label="Email")
    class Meta:
        model = Account
        fields = ['account_type', 'telefon', 
            'password1', 'password2', 'username', 'first_name', 'last_name', 'email'
        ]

    def clean(self):
        """
        This method verifies that the values entered in the form
        are valid.
        For example we check if the password the user entered into
        the field password1 and password1 match.
        NOTE : Errors will  appear in non_field_errors() because
        it applies to more than one field.
        """
        cleaned_data = super(RegistrationForm, self).clean()
        if 'password1' in cleaned_data and 'password2' in cleaned_data:
            if cleaned_data['password1'] != cleaned_data['password2']:
                raise forms.ValidationError("Les mots ne correspondent pas.\
                Veuillez verifier que les deux champs sont identiques.")
            else:
                print("RegistrationForm : Password is valid")
        else:
            print("RegistrationForm is invalid: password error")
        return cleaned_data

    def save(self, commit=True):
        account = super(RegistrationForm, self).save(commit=False)
        user = account.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        user.set_password(self.cleaned_data['password1'])
        if commit:
            account.save()
        return account
    

