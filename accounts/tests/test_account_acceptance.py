from django.test import TestCase
from django.contrib.auth.models import User
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from accounts.models import Account
from accounts.account_services import AccountService

import time
import unittest


class UserAccountTest(TestCase):
    """
    Acceptance Tests.
    Verify if has access to the application.
    """
    def test_user_can_create_account(self):
        self.fail("Not implemented yet")
    

    def test_user_can_login(self):
        self.fail("Not implemented yet")

    def test_user_can_logout(self):
        self.fail("Not implemented yet")
    




        
