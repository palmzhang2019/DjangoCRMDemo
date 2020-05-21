from django.shortcuts import render, HttpResponse
from rbac.models import User
from rbac.service.permission import initialsession
# Create your views here.


def login(request):
    if request.method == "POST":
        user = request.POST.get("user")
        pwd = request.POST.get("pwd")

        user = User.objects.filter(name=user, pwd=pwd).first()
        if user:
            request.session["user_id"] = user.pk
            # 注册权限到session中
            initialsession(user, request)
            return HttpResponse("登陆成功！")


    return render(request, "login.html")
