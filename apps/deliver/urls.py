from django.conf.urls import url
from django.urls import path, re_path

from apps.deliver import views
from apps.deliver.views import RegisterView, LoginView, DeliverInfoView, LogoutView, OrderInfoView, DeliverMapView, \
    DeliverStatusView, OrderInfo1View, MMapView, AMapView
from apps.user.views import UserInfoOrder

urlpatterns = [
    # path('', views.index, name='index'),
    path('register1/', RegisterView.as_view(), name='register1'),
    path('login1/', LoginView.as_view(), name='login1'),
    re_path('^$', DeliverInfoView.as_view(), name='deliver1'),  # 用户中心-信息页
    path('logout1/', LogoutView.as_view(), name='logout1'),
    # re_path('info/(?P<page>\d+)$', OrderInfoView.as_view(), name='info')
    # re_path('info/', OrderInfoView.as_view(), name='info'),
    re_path('^dstatus/(?P<order_id>.*)$', DeliverStatusView.as_view(), name='dstatus'),
    # path('dstatus/', DeliverStatusView.as_view(), name='dstatus'),
    path('zmap/', MMapView.as_view(), name='zmap'),
    path('amap/', AMapView.as_view(), name='amap'),
    re_path('^map/(?P<order_id>.*)$', DeliverMapView.as_view(), name='map'),
    # re_path('^comment/(?P<order_id>.*)$', CommentView.as_view(), name='comment'),
    re_path('info1/', OrderInfo1View.as_view(), name='info1'),
    re_path('info/(?P<page>\d+)$', OrderInfoView.as_view(), name='info')
]
