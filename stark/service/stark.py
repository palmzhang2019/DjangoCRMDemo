# by luffycity.com
import json

from django.conf.urls import url
from django.db.models import Q
from django.shortcuts import HttpResponse,render,redirect
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.forms import ModelForm, widgets as wid
from stark.utils.page import Pagination
import copy
from django.db.models.fields.related import ManyToManyField, ForeignKey
from django.forms.models import ModelMultipleChoiceField, ModelChoiceField


class ShowList(object):
    def __init__(self, config, data_list, request):
        self.config = config
        self.data_list = data_list
        self.request = request
        # 分页
        dataCount = self.data_list.count()
        current_page = int(self.request.GET.get("page", 1))
        base_path = self.request.path
        self.pagination = Pagination(
            current_page,
            dataCount,
            base_path,
            self.request.GET,
            per_page_num = 10,
            pager_count = 9
        )
        self.page_data = self.data_list[self.pagination.start:self.pagination.end]
        self.acitons = self.config.new_actions()

    def get_filter_linktags(self):
        link_dict = {}
        for filter_field in self.config.list_filter:
            params = copy.deepcopy(self.request.GET)
            # 用于后台判断是否是点击的filter。我准备用juery来写，所以这里注释掉
            # cid = self.request.GET.get(filter_field)
            filter_field_obj = self.config.model._meta.get_field(filter_field)

            if isinstance(filter_field_obj, ForeignKey) or isinstance(filter_field_obj,ManyToManyField):
                data_list = filter_field_obj.rel.to.objects.all()
            else:
                data_list = self.config.model.objects.all().values("pk", filter_field)
            temp = []

            # 处理全部标签
            if params.get(filter_field):
                del params[filter_field]
            temp.append('<a href="?{}">全部</a>'.format(params.urlencode()))
            #
            for item in data_list:
                if isinstance(filter_field_obj, ForeignKey) or isinstance(filter_field_obj, ManyToManyField):
                    pk = item.pk
                    text = str(item)
                    params[filter_field] = pk
                else:
                    pk = item.get("pk")
                    text = item.get(filter_field)
                    params[filter_field] = text
                _url = params.urlencode()
                link_tag = '<a href="?{}">{}</a>'.format(_url, text)
                temp.append(link_tag)
            link_dict[filter_field] = temp
        return link_dict

    def get_action_list(self):
        temp = []
        for action in self.acitons:
            temp.append({
                "name": action.__name__,
                "desc": action.short_description
            })
        return temp

    def get_header(self):
        header_list = list()
        for filed in self.config.new_list_play():
            if callable(filed):
                val = filed(self.config, header=True)
                header_list.append(val)
            elif filed == "__str__":
                header_list.append(self.config.model._meta.model_name.upper())
            else:
                val = self.config.model._meta.get_field(filed).verbose_name
                header_list.append(val)
        return header_list

    def get_body(self):
        app_label = self.config.model._meta.app_label
        model_name = self.config.model._meta.model_name

        new_data_list=[]
        for obj in self.page_data:
            temp=[]
            for filed in self.config.new_list_play():# ["pk","name","age",edit]
                if callable(filed):
                    # 自定义方法都走这里
                    # 因为这里的filed是没有括号的，是一个callable对象，所以是可以通过变量来进行运算的。
                    val=filed(self.config,obj)
                else:
                    try:
                        #这里是字符串显示的
                        field_obj = self.config.model._meta.get_field(filed)
                        if isinstance(field_obj, ManyToManyField):
                            ret = getattr(obj, filed).all()
                            t = []
                            for i in ret:
                                t.append(str(i))
                            val = ",".join(t)
                        elif field_obj.choices:
                            val = getattr(obj, "get_"+filed+"_display")
                        else:
                            val=getattr(obj,filed)
                        if filed in self.config.list_display_links:
                            _url = reverse("%s_%s_change" % (app_label, model_name), args=(obj.pk,))
                            val = mark_safe("<a href='%s'>%s</a>" % (_url, val))
                    except:
                        val = getattr(obj, filed)
                temp.append(val)
            new_data_list.append(temp)
        return new_data_list

class ModelStark(object):
    list_display=["__str__"]
    list_display_links = []
    modelform_class = None
    search_fields = []
    actions = []
    list_filter = []

    def patch_delete(self, request, queryset):
        queryset.delete()
    patch_delete.short_description = "批量删除"

    def new_actions(self):
        temp = []
        temp.append(ModelStark.patch_delete)
        temp.extend(self.actions)
        return temp

    def __init__(self,model,site):
        self.model=model
        self.site=site

    def edit(self, obj = None, header=False):
        if header:
            return "操作"
        model_name = self.model._meta.model_name
        app_label = self.model._meta.app_label
        _url = reverse("%s_%s_change" % (app_label, model_name), args=(obj.pk,))
        return mark_safe("<a href='%s'>编辑</a>" % _url)

    def delete(self, obj = None, header = False):
        if header:
            return "操作"
        return mark_safe("<a href='%s/delete'>删除</a>" %obj.pk)

    def getModelFormClass(self):
        if not self.modelform_class:
            class ModelFormDemo(ModelForm):
                class Meta:
                    model = self.model
                    fields = "__all__"
            return ModelFormDemo
        else:
            return self.modelform_class

    from django.forms.boundfield import BoundField
    def add_view(self, request):
        modelform_class = self.getModelFormClass()
        form = modelform_class()
        for ifield in form:
            if isinstance(ifield.field, ModelMultipleChoiceField) or isinstance(ifield.field, ModelChoiceField):
                ifield.is_pop = True
                app_label = ifield.field.queryset.model._meta.app_label
                model_name = ifield.field.queryset.model._meta.model_name
                ifield.url = reverse("%s_%s_add" %(app_label, model_name))+"?pop_res_id=id_%s" % ifield.name

        if request.method == "POST":
            form = modelform_class(request.POST)
            if form.is_valid():
                obj = form.save()

                pop_res_id = request.GET.get("pop_res_id", "")
                if pop_res_id:
                    res = {"pk": obj.pk, "text": str(obj), "pop_res_id": pop_res_id}
                    return render(request, "pop.html", locals())
                else:
                    return redirect(self.get_list_url())
            return render(request, "add_view.html", locals())

        return render(request, "add_view.html", locals())

    def change_view(self, request, id):
        ModelFormDemo = self.getModelFormClass()
        editObj = self.model.objects.filter(pk=id).first()
        if request.method == "POST":
            form = ModelFormDemo(request.POST, instance=editObj)
            if form.is_valid():
                form.save()
                return redirect(self.get_list_url())
            return render(request, "change_view.html", locals())

        form = ModelFormDemo(instance = editObj)
        return render(request, "change_view.html", locals())

    def delete_view(self, request, id):
        url = self.get_list_url()
        if request.method == "POST":
            self.model.objects.filter(pk=id).delete()
            return redirect(url)
        return render(request, "delete_view.html", locals())

    def checkbox(self, obj = None, header=False):
        if header:
            return mark_safe('<input id="choice" type="checkbox">')
        return mark_safe("<input class='choice_item' type='checkbox' name='selected_pk' value='%s'>" % obj.pk)

    def new_list_play(self):
        temp = []
        temp.append(ModelStark.checkbox)
        temp.extend(self.list_display)
        if not self.list_display_links:
            temp.append(ModelStark.edit)
        temp.append(ModelStark.delete)
        return temp

    def get_search(self, request):
        search_connection = Q()
        keyword = request.GET.get("search", "")
        self.keyword = keyword
        if keyword:
            search_connection.connector = "or"
            for search_field in self.search_fields:
                search_connection.children.append((search_field+"__contains", keyword))
        return search_connection

    def get_filter(self, request):
        filter_condition = Q()
        for filter_field, val in request.GET.items():
            if filter_field != "page":
                filter_condition.children.append((filter_field, val))
        return filter_condition

    def list_view(self, request):
        if request.method == "POST":
            action = request.POST.get("action")
            selected_pk = request.POST.getlist("selected_pk")
            # 反射，按方法名找类中的函数
            action_func = getattr(self, action)
            query_set = self.model.objects.filter(pk__in=selected_pk)
            action_func(request, query_set)

        # 获取search的Q对象
        search_connection = self.get_search(request)
        # 获取filter的Q对象
        filter_condition = self.get_filter(request)

        data_list = self.model.objects.all().filter(search_connection).filter(filter_condition)
        showListView = ShowList(self, data_list, request)
        #
        # # 构建查看URL
        add_url = self.get_add_url()
        return render(request, "list_view.html", locals())

    def get_add_url(self):
        model_name = self.model._meta.model_name
        app_label = self.model._meta.app_label
        _url = reverse("%s_%s_add" % (app_label, model_name))
        return _url

    def get_list_url(self):
        model_name = self.model._meta.model_name
        app_lable = self.model._meta.app_label
        _url = reverse("%s_%s_list" % (app_lable, model_name))
        return _url

    def extra_url(self):
        return []

    def get_urls_2(self):
        # self代表当前配置类的对象
        temp = []

        model_name=self.model._meta.model_name
        app_label=self.model._meta.app_label

        temp.append(url(r"^add/", self.add_view,name="%s_%s_add"%(app_label,model_name)))
        temp.append(url(r"^(\d+)/delete/", self.delete_view,name="%s_%s_delete"%(app_label,model_name)))
        temp.append(url(r"^(\d+)/change/", self.change_view,name="%s_%s_change"%(app_label,model_name)))
        temp.append(url(r"^$", self.list_view,name="%s_%s_list"%(app_label,model_name)))
        temp.extend(self.extra_url())
        return temp

    @property
    def urls_2(self):
        return self.get_urls_2(), None, None

class StarkSite(object):
    def __init__(self):
        self._registry={}

    def register(self,model,stark_class=None):
        if not stark_class:
            stark_class=ModelStark

        self._registry[model] = stark_class(model, self)


    def get_urls(self):
        temp=[]
        for model,stark_class_obj in self._registry.items():
            model_name=model._meta.model_name
            app_label=model._meta.app_label
            # 分发增删改查
            temp.append(url(r"^%s/%s/"%(app_label,model_name),stark_class_obj.urls_2))

        return temp

    @property
    def urls(self):

       return self.get_urls(),None,None
site=StarkSite()












