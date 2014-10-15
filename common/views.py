#!usr/bin/env python
#coding: utf-8
from django.shortcuts import render_to_response,get_object_or_404
from django.template import RequestContext
from django.contrib import messages
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import HttpResponseBadRequest
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login ,logout as auth_logout



from utils.constants import account_usertype_dict

from django.contrib.auth.models import User
from log.models import Log
from authority.models import Role


@login_required
def index(request):
    return render_to_response('common/index.html', {'account_usertype_dict':account_usertype_dict}, context_instance=RequestContext(request))


# 跳转到登录页
def loginpage(request):
    # 登录成功跳转到用户的原请求页
    jump_to = request.GET.get('next')
    if not jump_to:
        jump_to = '/'
    return render_to_response('common/login.html',
                              {'next':jump_to},
                              context_instance=RequestContext(request))


# 登录    
def login(request):
    if request.POST:
        username = request.POST.get("username")
        password = request.POST.get("password")
        jump_to = request.POST.get("next")
        # 验证用户名密码
        res = login_core(request, username.strip(), password.strip())
        if res:
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
            #重定向到首页
            return HttpResponseRedirect(jump_to)
        else:
            Log(username=username, content="execute login user error!", level=1).save()
            return render_to_response("common/login.html", { "message":u"登录失败", 'next':'/'}, context_instance=RequestContext(request))
     
    else:
        return  HttpResponseBadRequest(u"错误请求")


# 登录核心方法 注意特殊用户 admin
def login_core(request, username, password):
    user = authenticate(username=username, password=password)
    # 登陆核心方法
    if user:
        if user.is_active:
            auth_login(request, user)
            ret = True
        else:
            messages.add_message(request, messages.INFO, _(u'用户没有激活'))
    else:
        messages.add_message(request, messages.INFO, _(u'用户不存在'))
        ret = False
    return ret


@login_required
def logout(request):
    username = request.user.username
    # 注销
    auth_logout(request)
    Log(username=username, log_type=0, content="execute logout user success!", level=1).save()
    return render_to_response("common/login.html", {'next':'/'}, context_instance=RequestContext(request))
    
# 通用的函数，表示相应处理操作已成功
@login_required
def success(request):

    return render_to_response("common/success.html")
   



@login_required
def nav_index(request):
    if request.user.is_authenticated():
        # 从request中取值
        username = request.user.username
    return render_to_response('common/nav_index.html', {}, context_instance=RequestContext(request))

@login_required
def nav_resource(request):
    return render_to_response('common/nav_resource.html', {}, context_instance=RequestContext(request))

@login_required
def nav_log(request):
    return render_to_response('common/nav_log.html', {}, context_instance=RequestContext(request))

@login_required
def nav_ippool(request):
    return render_to_response('common/nav_ippool.html', {}, context_instance=RequestContext(request))

@login_required
def nav_user(request):
    return render_to_response('common/nav_user.html', {}, context_instance=RequestContext(request))

@login_required
def nav_authority(request):
    return render_to_response('common/nav_authority.html', {}, context_instance=RequestContext(request))

@login_required
def main(request):
    return render_to_response('common/main.html', {}, context_instance=RequestContext(request))

