from accounts.models import Account


def account_context(request):
    context = {
        'account' : None
    }
    if request.user.is_authenticated:
        try:
            account = Account.objects.get(user=request.user)
            context['account'] = account
        except Account.DoesNotExist :
            pass
        
    return context