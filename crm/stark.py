import datetime

from django.utils.safestring import mark_safe
from django.conf.urls import url
from stark.service.stark import site, ModelStark
from .models import *
from django.shortcuts import HttpResponse, redirect, render
from django.http import JsonResponse
from django.db.models import Q


site.register(School)

class UserConfig(ModelStark):
    list_display = ["name", "email", "depart"]
site.register(UserInfo, UserConfig)

class ClassConfig(ModelStark):

    def display_classname(self, obj=None, header=False):
        if header:
            return "班级名称"
        class_name = "%s(%s)" % (obj.course.name, str(obj.semester))
        return obj.__str__

    list_display = [display_classname, "tutor", "teachers"]

site.register(ClassList, ClassConfig)

class CustomerConfig(ModelStark):
    # obj表示当前这张表
    def display_gender(self, obj = None, header = False):
        if header:
            return "性别"
        return obj.get_gender_display()

    def get_course(self, obj = None, header = False):
        if header:
            return "咨询课程"
        course = obj.course.all()

        temp = ['<a href="/stark/crm/customer/cancel_course/{}/{}" style="border:1px solid #369; padding:3px 6px" ><span>{}</span></a>'
                    .format(obj.pk, cour.pk, cour.name) for cour in course]
        tempstr = " ".join(temp)
        return mark_safe(tempstr)

    def cancel_course(self, request, customer_id, course_id):
        # 找到对应的用户对象
        obj = Customer.objects.filter(pk=customer_id).first()
        # 删掉当前用户对象中的课程对象
        obj.course.remove(course_id)
        return redirect(self.get_list_url())

    def public_customer(self, request):
        # 未报名的 & 3天未跟进 | 15天未成单
        now = datetime.datetime.now()
        #3天未跟进
        not_connect = now - datetime.timedelta(days=3)
        #15天未成单
        not_success = now - datetime.timedelta(days=15)
        user_id = 0
        customer_list = Customer.objects.filter\
            (Q(last_consult_date__lt = not_connect)|Q(recv_date__lt=not_success),status=2)\
        .exclude(consultant=user_id)
        return render(request, "public.html", locals())

    def further(self, request, customer_id):
        user_id = 3
        now = datetime.datetime.now()
        update = {
            "consultant": user_id,
            "recv_date": now,
            "last_consult_date": now
        }
        #3天未跟进
        not_connect = now - datetime.timedelta(days=3)
        #15天未成单
        not_success = now - datetime.timedelta(days=15)
        # 为该客户更改课程顾问和对应的时间
        ret = Customer.objects.filter(pk=customer_id).filter(Q(last_consult_date__lt = not_connect)|Q(recv_date__lt=not_success)).update(**update)
        if not ret:
            return HttpResponse("已经被跟进了")
        # 更改客户分布状态
        CustomerDistribute.objects.create(customer_id=customer_id, consultant_id=user_id, date=now)
        return HttpResponse("跟进成功")

    def mycustomer(self, request):
        user_id = 2
        customer_distribute_list = CustomerDistribute.objects.filter(consultant_id = user_id)
        return render(request, "mycustomer.html", locals())

    def extra_url(self):
        temp = []
        temp.append(url(r"cancel_course/(\d+)/(\d+)/", self.cancel_course))
        temp.append(url(r"public/", self.public_customer))
        temp.append(url(r'further/(\d+)', self.further))
        temp.append(url(r'mycustomer/', self.mycustomer))
        return temp

    list_display = ["name", display_gender, "consultant", get_course]
site.register(Customer, CustomerConfig)
site.register(Department)
site.register(Course)

class ConsultrecordConfig(ModelStark):
    list_display = ['customer', 'consultant', 'date', 'note']
site.register(ConsultRecord, ConsultrecordConfig)

class CourseRecordConfig(ModelStark):

    def score(self, request, course_record_id):
        if request.method == "POST":
            data = {}
            for key, value in request.POST.items():
                if key == "csrfmiddlewaretoken":
                    continue
                filed, pk = key.rsplit('_',1)
                if pk in data:
                    data[pk][filed] = value
                else:
                    data[pk] = {filed:value}

            for pk, update_data in data.items():
                StudyRecord.objects.filter.update(**update_data)
            return redirect(request.path)

        else:
            study_record_list = StudyRecord.objects.filter(course_record=course_record_id)
            score_choices = StudyRecord.score_choices

            return render(request, "score_input.html", locals())

    def extra_url(self):
        temp = []
        temp.append(url(r"record_score/(\d+)/", self.score))
        return temp

    def patch_studyrecord(self,request, querysets):
        for course_record in querysets:
            # student_list = Student.objects.filter(class_list__id=course_record.class_obj.pk)
            student_list = Student.objects.filter(class_list__courserecord = course_record)
            temp = []
            for student in student_list:
                obj = StudyRecord(student=student, course_record=course_record)
                temp.append(obj)
            StudyRecord.objects.bulk_create(temp)

    def record(self, obj=None, header=False):
        if header:
            return "记录"
        return mark_safe('<a href="/stark/crm/studyrecord/?course_record={}">记录</a>'.format(obj.pk))

    def record_score(self, obj = None, header=False):
        if header:
            return "录入成绩"
        return mark_safe('<a href="record_score/{}">录入成绩</a>'.format(obj.pk))

    list_display = ['class_obj', 'day_num', 'teacher', record, record_score]

    patch_studyrecord.short_description = "批量生成学生学习记录"
    actions = [patch_studyrecord]
site.register(CourseRecord, CourseRecordConfig)

class StudyrecordConfig(ModelStark):

    def patch_late(self, request, queryset):
        queryset.update(record="late")
    patch_late.short_description = "迟到"
    actions = [patch_late]

    list_display = ["student", 'course_record', "record", "score"]
site.register(StudyRecord, StudyrecordConfig)

class StudentConfig(ModelStark):

    def extra_url(self):
        # extral_url是通过ModelStark父类路由get_urls_2传入的
        temp = []
        temp.append(url(r'score_show/(\d+)', self.score_view))
        return temp

    def score_view(sel, request, student_id):

        if request.is_ajax():
            student_id = request.GET.get("student_id")
            class_id = request.GET.get("class_id")
            study_record_list = StudyRecord.objects.filter(student=student_id, course_record__class_obj=class_id)
            data_list = []

            for study_record in study_record_list:
                day_num = study_record.course_record.day_num
                data_list.append(["day{}".format(day_num), study_record.score])
            return JsonResponse(data_list, safe=False)
        else:
            # studyrecord__scores = Student.objects.filter(pk=student_id).values("studyrecord__course_record", "studyrecord__score")
            student = Student.objects.filter(pk=student_id).first()
            class_list = student.class_list.all()
            return render(request, "score_view.html", locals())

    def score_show(self, obj=None, header = False):
        # 这里的obj是来自service/stark.py中page_data中循环的的obj
        # 调用的是service/stark.py val=filed(self.config,obj)
        # self.config 传入了self, obj传入了obj
        if header == True:
            return "查看成绩"
        return mark_safe('<a href="score_show/{}">查看成绩</a>'.format(obj.pk))

    list_display = ['customer', 'class_list', score_show]
site.register(Student, StudentConfig)
site.register(CustomerDistribute)