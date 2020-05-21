def initialsession(userObj, request):
    # 方案一
    # ret = userObj.roles.all().values("permissons__url").distinct()
    # permission_list = list()
    # for r in ret:
    #     permission_list.append(r.get('permissons__url'))
    # request.session["permission_list"] = permission_list

    # 方案2
    rets = userObj.roles.all().values("permissons__url", "permissons__group", "permissons__action").distinct()
    pdict = dict()
    for ret in rets:
        gid = ret.get("permissons__group")
        if gid not in pdict.keys():
            pdict[gid] = dict()
        if "urls" not in pdict[gid]:
            pdict[gid]['urls'] = list()
        pdict[gid]['urls'].append(ret['permissons__url'])
        if "actions" not in pdict[gid]:
            pdict[gid]['actions'] = list()
        pdict[gid]['actions'].append(ret['permissons__action'])
    request.session['permission_dict'] = pdict

    # 注册表单权限
    permissions = userObj.roles.all().values("permissons__url", "permissons__action", "permissons__title").distinct()

    menuPermissionList = []
    for item in permissions:
        if item["permissons__action"] == "list":
            menuPermissionList.append((item['permissons__url'], item['permissons__title']))
    request.session["menuPermissionList"] = menuPermissionList
