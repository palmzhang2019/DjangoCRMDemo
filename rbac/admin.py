from django.contrib import admin
from .models import *
# Register your models here.


class PersonConfig(admin.ModelAdmin):
    list_display = ["title", "url", "group", "action"]

admin.site.register(User)
admin.site.register(Permission, PersonConfig)
admin.site.register(Role)
admin.site.register(PermissionGroup)