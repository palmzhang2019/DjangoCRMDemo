from django import template

register = template.Library()

@register.inclusion_tag("menu.html")
def get_menu(request):
    menuPermissionList = request.session.get("menuPermissionList")
    return {
        "menuPermissionList": menuPermissionList
    }
