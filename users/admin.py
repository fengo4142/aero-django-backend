from django.contrib import admin
from django_reverse_admin import ReverseModelAdmin
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django.contrib.auth.models import User, Permission
import logging
from users.models import AerosimpleUser, Role, PermissionConfig

logger = logging.getLogger('backend')


class PermissionConfigAdmin(admin.ModelAdmin):
    filter_horizontal = ('permissions',)


class UserForm(ModelForm):
    class Meta:
        """Meta."""

        model = User
        fields = ('email',)

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.fields['email'].required = True

    def clean(self):
        if self.instance.pk is None:
            exists = User.objects.filter(
                email=self.cleaned_data['email']).exists()
            if exists:
                raise ValidationError({
                    'email': "this email already exists"
                })


class AerosimpleUserAdmin(ReverseModelAdmin):
    filter_horizontal = ('roles',)
    inline_type = 'stacked'
    exclude=['airport',]
    extra = 0
    search_fields = ('first_name', 'last_name', 'user__email', 'authorized_airports__code')
    list_display = ('first_name', 'last_name', 'email', 'airport_codes')
    inline_reverse = (
        'user', {
            'classes': ('wide',),
            'form': UserForm,
            'fields': ('email',),
        }),


admin.site.register(AerosimpleUser, AerosimpleUserAdmin)
admin.site.register(Role)
# admin.site.register(Permission)
admin.site.register(PermissionConfig, PermissionConfigAdmin)
