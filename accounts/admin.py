from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from accounts.models import Account

# Register your models here.

class AccountInline(admin.StackedInline):
    model = Account
    can_delete = False
    fk_name = 'user'
    verbose_name_plural = 'Profile'
    

class AccountAdmin(admin.ModelAdmin):
    inlines = [AccountInline]
    #list_display = ['balance', 'country', 'city', 'telefon', 'created_by']
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(AccountAdmin, self).get_inline_instances(request, obj)



admin.site.unregister(User)
admin.site.register(User ,AccountAdmin)
admin.site.register(Account)
