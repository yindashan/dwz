#!usr/bin/env python
#coding: utf-8
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.shortcuts import render_to_response, get_object_or_404
from django.core.context_processors import csrf
from django.views.decorators.csrf import csrf_protect
from django.template import RequestContext
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, login as auth_login ,logout as auth_logout
from django.utils.translation import ugettext_lazy as _
from django.utils import simplejson
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.contrib.auth.decorators import login_required

import json
#from django.conf import settings
#from_email = settings.DEFADEFAULT_FROM_EMAIL
from django.template import loader

from utils.utils import send_mail

from log.models import Log
from authority.models import Role

from utils.constants import account_usertype_dict

# 导入在forms.py 中定义的所有表单类。
from forms import *
from account.models import UserProfile

@login_required
def index(request):
    retdir = {}
    users = User.objects.order_by('-id')
    if 'query' in request.POST and request.POST['query']:
        query = request.POST['query']
        retdir['query'] = query
        users = users.filter(username__icontains = query)
    if 'numPerPage' in request.POST and request.POST['numPerPage']:
        numPerPage = request.POST['numPerPage']
    else:
        numPerPage = 10
    paginator = Paginator(users, numPerPage)
    page = request.POST.get('pageNum', 1)
    try:
        if int(page) > paginator.num_pages:
            page = str(paginator.num_pages)
        users = paginator.page(page)
    except (EmptyPage, InvalidPage):
        users = paginator.page(paginator.num_pages)
    tmpdir = {'users':users,'currentPage':page, 'numPerPage':numPerPage, 'account_usertype_dict':account_usertype_dict}
    retdir.update(tmpdir)
    return render_to_response('account/welcome.html', retdir, context_instance=RequestContext(request))
    

@login_required
def info(request, id):
    user=get_object_or_404(User,pk=int(id))
    return render_to_response('account/info.html', {'user': user, 'account_usertype_dict':account_usertype_dict}, context_instance=RequestContext(request))

@login_required
def register(request):

    if request.POST:
        username = request.POST.get('org.username',None)
        password = request.POST.get('password',None)
        confirmpwd = request.POST.get('confirmpwd',None)
        password = username
        confirmpwd = username
        email = request.POST.get('org.email',None)
        
        role_name_str = request.POST.get('org.role_name', None)
        
        department = request.POST.get('org.parent_organization_name',None)
        
        
        phone = request.POST.get('phone',None)
        '''验证重复帐号名'''
        usernames = User.objects.filter(username__iexact=username)
        '''验证重复email'''
        emails = User.objects.filter(email__iexact=email)
        if usernames:
            return HttpResponse(simplejson.dumps({"statusCode":302, "navTabId":request.POST.get('navTabId','accountindex'), "callbackType":request.POST.get('callbackType',None), "message":u'用户名已经存在不能添加', "info":u'用户名已经存在不能添加',"result":u'用户名已经存在不能添加'}), mimetype='application/json')
        
        
        '''验证两次输入密码是否一致'''
        if password != confirmpwd:
            return HttpResponse(simplejson.dumps({"statusCode":302, "navTabId":request.POST.get('navTabId','accountindex'), "callbackType":request.POST.get('callbackType',None), "message":u'两次密码输入不一致', "info":u'两次密码输入不一致',"result":u'两次密码输入不一致'}), mimetype='application/json')
        
        if emails:
            return HttpResponse(simplejson.dumps({"statusCode":302, "navTabId":request.POST.get('navTabId','accountindex'), "callbackType":request.POST.get('callbackType',None), "message":u'EMAIL已经存在不能添加', "info":u'EMAIL已经存在不能添加',"result":u'EMAIL已经存在不能添加'}), mimetype='application/json')
        if password != None and password != '':
            password = make_password(password, salt=None, hasher='default')
            user = User(username=username, password=password, email=email)
        else:
            user = User(username=username, email=email)
        user.save()
        userprofile = UserProfile(user=user, department=department, phone=phone)
        userprofile.save()
        
        if role_name_str != None and role_name_str != '':
            role_name_list = role_name_str.split(',')
            for role_name in role_name_list:
                if role_name != None and role_name != '':
                    try:
                        role = Role.objects.get(role_name__exact=role_name)
                        role.users.add(user)
                    except:
                        return HttpResponse(simplejson.dumps({"statusCode":302, "navTabId":request.POST.get('navTabId','accountindex'), "callbackType":request.POST.get('callbackType',None), "message":u'存在无效角色名请重新选择或置空'}), mimetype='application/json')
        
        
        Log(username=request.user.username, content=u"成功创建用户: " + username, level=1).save()
        return HttpResponse(simplejson.dumps({"statusCode":200, "navTabId":request.POST.get('navTabId','accountindex'), "callbackType":request.POST.get('callbackType','closeCurrent'), "message":u'添加成功'}), mimetype='application/json')
    else:
        return render_to_response('account/register.html', {'account_usertype_dict':account_usertype_dict})
    
@login_required
def edit(request, id):
    user = get_object_or_404(User,pk=int(id))
    userprofile=get_object_or_404(UserProfile,user_id=int(id))
    if request.POST:
        user.username = request.POST.get('username',None)
        password = request.POST.get('password',None)
        password = user.username
        if password != None and password != '':
            user.password = make_password(password, salt=None, hasher='default')
        
        role_name_str = request.POST.get('org.role_name', None)
        
        user.email = request.POST.get('email',None)
        department = request.POST.get('org.parent_organization_name',None)
        
        userprofile.department = department
        userprofile.phone = request.POST.get('phone',None)
        user.save()
        userprofile.save()
        
        roles = user.role_set.all()
        for role in roles:
            role.users.remove(user)
        if role_name_str != None and role_name_str != '':
            role_name_list = role_name_str.split(',')
            for role_name in role_name_list:
                if role_name != None and role_name != '':
                    try:
                        role = Role.objects.get(role_name__exact=role_name)
                        role.users.add(user)
                    except:
                        return HttpResponse(simplejson.dumps({"statusCode":302, "navTabId":request.POST.get('navTabId','accountindex'), "callbackType":request.POST.get('callbackType',None), "message":u'存在无效角色名请重新选择或置空'}), mimetype='application/json')
            
        Log(username=request.user.username, content=u"成功修改用户: " + user.username, level=1).save()
        return HttpResponse(simplejson.dumps({"status":1, "statusCode":200, "navTabId":request.POST.get('navTabId','accountindex'), "callbackType":request.POST.get('callbackType','closeCurrent'), "message":u'编辑成功', "info":u'编辑成功',"result":u'编辑成功'}), mimetype='application/json')
    
    roles = user.role_set.all()
    role_list = []
    for role in roles:
        role_list.append(role.role_name)
    retdir = {'user': user, 'account_usertype_dict':account_usertype_dict, 'role_list':role_list}
    return render_to_response('account/edit.html', retdir, context_instance=RequestContext(request))
    
        
def login(request):
    '''登陆视图'''
    template_var={}
    form = LoginForm()
    if request.method == 'POST':
        form = LoginForm(request.POST.copy())
        if form.is_valid():
            ret = False
            ret = _login(request,form.cleaned_data["username"],form.cleaned_data["password"])
            if ret:
                '''
                    获取用户对应的所有角色,根据角色生成相应的权限列表并把权限列表放到session里面
                '''
                roles = request.user.role_set.all()
                # 模块权限列表
                authority_list_module = []
                # 功能按钮权限列表
                authority_list_button = []
                # 模块字段权限列表
                authority_list_modulefield = []
                
                for role in roles:
                    modules = role.modules.all()
                    buttons = role.buttons.all()
                    modulefields = role.modulefields.all()
                    for module in modules:
                        auth_identify = module.module_type
                        if auth_identify not in authority_list_module:
                            authority_list_module.append(auth_identify)
                    for button in buttons:
                        auth_identify = button.module.module_type + button.button_type
                        if auth_identify not in authority_list_button:
                            authority_list_button.append(auth_identify)
                    for modulefield in modulefields:
                        auth_identify = modulefield.module.module_type + modulefield.modulefield_type
                        if auth_identify not in authority_list_modulefield:
                            authority_list_modulefield.append(auth_identify)
                        
                # 把权限列表放到session里面
                request.session["authority_list_module"] = authority_list_module
                request.session["authority_list_button"] = authority_list_button
                request.session["authority_list_modulefield"] = authority_list_modulefield
                    
                    
                # 获取登录IP
                RemoteIp = request.META.get('REMOTE_ADDR')
                Log(username=request.user.username, content=u"成功登录用户: " + request.user.username + u"，对应ip地址: " + RemoteIp, level=1).save()
                c = {'account_usertype_dict':account_usertype_dict}
                c.update(csrf(request))
                return render_to_response("common/index.html", c, context_instance=RequestContext(request))
            else:
                vardict = {
                    "message": u"登录失败！"
                }
                Log(username=form.cleaned_data["username"], content=u"用户登录失败！", level=1).save()
                vardict.update(csrf(request))
                return render_to_response("account/login.html", vardict, context_instance=RequestContext(request))
                
    template_var["form"]=form
    template_var.update(csrf(request))
    return render_to_response("account/login.html", template_var, context_instance=RequestContext(request))


def _login(request,username,password):
    '''登陆核心方法'''
    ret = False
    user = authenticate(username=username, password=password)
    if user:
        if user.is_active:
            auth_login(request, user)
            ret = True
        else:
            messages.add_message(request, messages.INFO, _(u'用户没有激活'))
    else:
        messages.add_message(request, messages.INFO, _(u'用户不存在'))
    return ret

@login_required
def logout(request):
    username = request.user.username
    '''注销视图'''
    auth_logout(request)
    Log(username=username, content=u"用户注销成功!", level=1).save()
    return render_to_response("account/login.html", {}, context_instance=RequestContext(request))

@login_required
def delete(request,id):
    user = User.objects.get(id=id)
    if request.user.is_authenticated():
        if request.user.username == user.username:
            return HttpResponse(simplejson.dumps({"statusCode":302, "navTabId":request.POST.get('navTabId','accountindex'), "callbackType":request.POST.get('callbackType',None), "message":u'不能删除自己'}), mimetype='application/json')
        else:
            Log(username=request.user.username, content=u"成功删除用户: " + user.username, level=1).save()
            user.delete()
    return HttpResponse(simplejson.dumps({"status":1, "statusCode":200, "navTabId":request.POST.get('navTabId','accountindex'), "callbackType":request.POST.get('callbackType',None), "message":u'删除成功', "info":u'删除成功',"result":u'删除成功'}), mimetype='application/json')

@login_required
def selecteddelete(request):
    ids = request.POST.get('ids', None)
    if ids:
        users = User.objects.extra(where=['id IN ('+ ids +')'])
        for user in users:
            if request.user.username == user.username:
                return HttpResponse(simplejson.dumps({"statusCode":302, "navTabId":request.POST.get('navTabId','accountindex'), "callbackType":request.POST.get('callbackType',None), "message":u'选中的用户组中包含自己不能批量删除'}), mimetype='application/json')
            Log(username=request.user.username, content=u"成功批量删除用户: " + user.username, level=1).save()
        users.delete()
        return HttpResponse(simplejson.dumps({"status":1, "statusCode":200, "navTabId":request.POST.get('navTabId','accountindex'), "callbackType":request.POST.get('callbackType',None), "message":u'删除成功', "info":u'删除成功',"result":u'删除成功'}), mimetype='application/json')




@login_required
def searchback_role(request):
    retdir = {}
    roles = Role.objects.order_by('-id')
    if 'query' in request.POST and request.POST['query']:
        query = request.POST['query']
        retdir['query'] = query
        roles = roles.filter(role_name__icontains = query)
    if 'numPerPage' in request.POST and request.POST['numPerPage']:
        numPerPage = request.POST['numPerPage']
    else:
        numPerPage = 10
    paginator = Paginator(roles, numPerPage)
    page = request.POST.get('pageNum', 1)
    try:
        if int(page) > paginator.num_pages:
            page = str(paginator.num_pages)
        roles = paginator.page(page)
    except (EmptyPage, InvalidPage):
        roles = paginator.page(paginator.num_pages)
    tmpdir = {'roles':roles,'currentPage':page, 'numPerPage':numPerPage}
    retdir.update(tmpdir)
    return render_to_response('account/searchback.html', retdir)



def autocomplete(request):
    if request.GET.has_key('q'):
        query = request.GET['q']
        if query != None:
            query = query.strip()
            users = User.objects.filter(username__icontains=query)
            return HttpResponse('\n'.join(user.username for user in users))
    return HttpResponse()
    

