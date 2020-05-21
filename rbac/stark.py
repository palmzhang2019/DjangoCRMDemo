from stark.service.stark import site
from .models import *
from stark.service.stark import ModelStark


site.register(User)
site.register(Role)

class PermissionConfig(ModelStark):
    list_display = ["title", "url", "group", "action"]
site.register(Permission, PermissionConfig)
site.register(PermissionGroup)