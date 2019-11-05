from django.urls import resolve
from django.test import TestCase
import unittest
#from django.contrib.auth import views as auth_views
from accounts import views


class AccountViewsUrlTest(TestCase):
    def test_account_root_url_resolve(self):
        found = resolve('/accounts/')
        self.assertEqual(found.func, views.user_account)

    def test_edit_account_url(self):
        found = resolve('/accounts/account-detail/10/')
        self.assertEqual(found.func, views.account_details)

    def test_update_account_url(self):
        found = resolve('/accounts/update/10/')
        self.assertEqual(found.func, views.account_update)
    

    def test_login_url(self):
        found = resolve('/accounts/login/')
        self.assertEqual(found.func, views.login)
    

    def test_logout_url(self):
        found = resolve('/accounts/logout/')
        self.assertEqual(found.func, views.logout)


    def test_password_change_url(self):
        found = resolve('/accounts/password-change/')
        self.assertEqual(found.func, views.password_change_views)
    

    def test_password_change_done_url(self):
        found = resolve('/accounts/password-change-done/')
        self.assertEqual(found.func, views.password_change_done_views)
    

    def test_register_url(self):
        found = resolve('/accounts/register/')
        self.assertEqual(found.func, views.register)
