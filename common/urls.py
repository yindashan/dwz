#!usr/bin/env python
#coding: utf-8
from django.conf.urls import patterns
from django.conf.urls import url

urlpatterns = patterns('',
    url(r'^$', 'common.views.index',name="index"),
    
    url(r'^index/$', 'common.views.index',name="common_index"),
    url(r'^login/$', 'common.views.login', name="common_login"),
    url(r'^logout/$', 'common.views.logout', name="common_logout"),
    url(r'^success/$', 'common.views.success',name="common_success"),
    
    url(r'^nav_index/$', 'common.views.nav_index', name="common_index"),
    url(r'^nav_resource/$', 'common.views.nav_resource', name="common_resource"),
    url(r'^nav_log/$', 'common.views.nav_log', name="common_log"),
    url(r'^nav_ippool/$', 'common.views.nav_ippool', name="common_ippool"),
    url(r'^nav_user/$', 'common.views.nav_user', name="common_user"),
    url(r'^nav_authority/$', 'common.views.nav_authority', name="common_authority"),
    
    url(r'^main/$', 'common.views.main', name="common_main"),
    
)