import re
from django.shortcuts import HttpResponse, redirect
from django.utils.deprecation import MiddlewareMixin


class VerifyPermission(MiddlewareMixin):
    def process_request(self, request):
        # 检查是否属于白名单
        valid_url_list = ['/login/', "/reg/", "/admin/.*"]
        for uri in valid_url_list:
            ret = re.match(uri, request.path_info)
            if ret:
                return None

        # 校验是否登陆
        user_id = request.session.get("user_id")
        if not user_id:
            return redirect("/login/")

        # 权限校验1
        # flag = False
        # for permission in request.session.get('permission_list', []):
        #     permission = "^%s$" % permission
        #     ret = re.match(permission, request.path_info)
        #     if ret:
        #         flag = True
        #         break
        # if not flag == True:
        #     return HttpResponse("没有访问权限！")

        # 权限校验2
        permission_dict = request.session.get("permission_dict")
        for item in permission_dict.values():
            urls = item['urls']
            for reg in urls:
                reg = "^%s$" % reg
                ret = re.match(reg, request.path_info)
                if ret:
                    request.actions = item['actions']
                    return None
        return HttpResponse("没有访问权限")