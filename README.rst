=====
Accounts
=====

Accounts is a Django app that add support for User Account. 
Detailed documentation is in the "docs" directory.

Quick start
-----------

1. Add "accounts" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'accounts',
    ]

2. Include the polls URLconf in your project urls.py like this::

    path('accounts/', include('accounts.urls')),

3. Run `python manage.py migrate` to create the accounts models.

4. Start the development server and visit http://127.0.0.1:8000/admin/
   to create a new account (you'll need the Admin app enabled).

5. Visit http://127.0.0.1:8000/accounts/ to access the the users accounts
