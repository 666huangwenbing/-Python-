from django.conf.urls import url
from django.urls import path, re_path
from .views import RegisterView, LoginView, UserInfoView, UserInfoOrder, AddressView
from apps.user import views
from django.contrib.auth.decorators import login_required

urlpatterns = [
    # path('register/',views.register)
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    re_path('^$', UserInfoView.as_view(), name='user'),  # 用户中心-信息页
    # path('order', UserInfoOrder.as_view(), name='order'),  # 用户中心-订单页
    path('address', AddressView.as_view(), name='address'),  # 用户中心-地址页
    re_path('order/(?P<page>\d+)$', UserInfoOrder.as_view(), name='order'),  # 用户中心-信息页
    # path('order',login_required(UserInfoOrder.as_view()),name='order'), # 用户中心-订单页
    # path('address',login_required(AddressView.as_view()),name='address'), # 用户中心-地址页
    path('sjfx/pie/', views.pie, name='pie'),
    path('sjfx/bar/', views.bar, name='bar'),
    path('sjfx/', views.sjfx, name='sjfx'),
    path('sjfx1/pie1/', views.pie1, name='pie1'),
    path('sjfx1/', views.sjfx1, name='sjfx1'),
    # path('page/', views.page_simple_layout(), name='page'),
    path('logout', LoginView.as_view(), name='logout')  # 注销登录
]
