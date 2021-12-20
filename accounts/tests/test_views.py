from django.urls import resolve
from django.test import TestCase
from django.utils import translation
import unittest
#from django.contrib.auth import views as auth_views
from accounts import views
CURRENT_LANGUAGE = translation.get_language()

class AccountViewsUrlTest(TestCase):
    def test_account_root_url_resolve(self):
        found = resolve(f'/{CURRENT_LANGUAGE}/accounts/')
        self.assertEqual(found.func, views.user_account)

    def test_edit_account_url(self):
        found = resolve(f'/{CURRENT_LANGUAGE}/accounts/account-detail/10/')
        self.assertEqual(found.func, views.account_details)

    def test_update_account_url(self):
        found = resolve(f'/{CURRENT_LANGUAGE}/accounts/update/10/')
        self.assertEqual(found.func, views.account_update)
    

    def test_login_url(self):
        found = resolve(f'/{CURRENT_LANGUAGE}/accounts/login/')
        self.assertEqual(found.func, views.login)
    

    def test_logout_url(self):
        found = resolve(f'/{CURRENT_LANGUAGE}/accounts/logout/')
        self.assertEqual(found.func, views.logout)


    def test_password_change_url(self):
        found = resolve(f'/{CURRENT_LANGUAGE}/accounts/password-change/')
        self.assertEqual(found.func, views.password_change_views)
    

    def test_password_change_done_url(self):
        found = resolve(f'/{CURRENT_LANGUAGE}/accounts/password-change-done/')
        self.assertEqual(found.func, views.password_change_done_views)
    

    def test_register_url(self):
        found = resolve(f'/{CURRENT_LANGUAGE}/accounts/register/')
        self.assertEqual(found.func, views.register)
