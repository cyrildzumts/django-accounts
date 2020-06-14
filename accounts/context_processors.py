from accounts.models import Account
import logging
logger = logging.getLogger(__name__)


def account_context(request):
    context = {
        'account' : None
    }
    if request.user.is_authenticated:
        try:
            account = Account.objects.get(user=request.user)
            context['account'] = account
        except Account.DoesNotExist :
            logging.warning(f"No account found for user {request.user.username}")
        
    return context