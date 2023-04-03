import numpy as np
from django.contrib import auth
from django.contrib.auth import authenticate, login, logout
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import View
from django.http import JsonResponse
from apps.deliver import models
from apps.deliver.models import Deliver
from apps.order.models import OrderInfo, OrderGoods
from apps.user.models import Address
from utils.mixin import LoginRequiredMixin
import datetime

class RegisterView(View):
    '''注册'''

    def get(self, request):
        '''显示注册页面'''
        return render(request, 'register1.html')

    def post(self, request):
        '''进行注册处理'''
        # 接收数据
        name = request.POST.get('name')
        password = request.POST.get('password')
        mobile = request.POST.get('mobile')
        allow = request.POST.get('allow')
        # info = Deliver.objects.filter(name=name, password=password, mobile=mobile)
        # 进行数据校验
        if not all([name, password, mobile]):
            # 数据不完整
            return render(request, 'register1.html', {'errmsg': '数据不完整'})

        if allow != 'on':
            return render(request, 'register1.html', {'errmsg': '请同意协议'})

        # 校验用户名是否重复
        try:
            deliver = Deliver.objects.get(name=name)
        except Deliver.DoesNotExist:
            # 用户名不存在
            deliver = None

        if deliver:
            # 用户名已存在
            return render(request, 'register1.html', {'errmsg': '用户名已存在'})

        # 进行业务处理: 进行用户注册
        deliver = models.Deliver.objects.create(name=name, password=password, mobile=mobile)
        # user.is_active = 0
        deliver.save()

        # 返回应答, 跳转到首页
        return redirect(reverse('deliver:login1'))
        # return render(request,'login1.html')


class LoginView(View):
    '''登录'''

    def get(self, request):
        '''显示登录页面'''
        # 判断是否记住了用户名
        if 'name' in request.COOKIES:
            name = request.COOKIES.get('name')
            checked = 'checked'
        else:
            name = ''
            checked = ''

        # 使用模板
        return render(request, 'login1.html', {'name': name, 'checked': checked})

    def post(self, request):
        '''登录校验'''
        # 接收数据
        name = request.POST.get('name')
        password = request.POST.get('password')
        mobile = request.POST.get('mobile')
        deliver = Deliver.objects.filter(name=name, password=password, mobile=mobile)
        # message = "所有字段都必须填写！"
        # 校验数据
        if not all([name, password]):
            return render(request, 'login1.html', {'errmsg': '数据不完整'})

        if deliver:
            request.session['IS_LOGIN'] = True
            request.session['name'] = name
            request.session['mobile'] = mobile

            return redirect(reverse('deliver:deliver1'))
        else:
            return render(request, 'login1.html')



class LogoutView(View):
    '''退出登录'''

    def get(self, request):
        '''退出登录'''
        # 清除用户的session信息
        # logout(request)
        # 跳转到登陆界面
        # return redirect(reverse('deliver:login1'))
        return render(request, 'login1.html')


class DeliverInfoView(LoginRequiredMixin, View):
    def get(self, request):
        is_login = request.session.get('IS_LOGIN', False)
        if is_login:
            name = request.session.get('name')
            mobile = request.session.get('mobile')
            return render(request, 'deliver_center_info.html', {'name': name, 'mobile': mobile})
        else:
            return render(request, 'login1.html')
        # return render(request, 'deliver_center.html', locals())
        # return render(request, 'deliver_center_info.html', {'info': info})


class OrderInfoView(LoginRequiredMixin, View):
    def get(self, request, page=None):
        is_login = request.session.get('IS_LOGIN', False)
        if is_login:
            name = request.session.get('name')
            mobile = request.session.get('mobile')

        num = int(name)
        orders = OrderInfo.objects.filter(sp2=num).order_by('order_id')
        now_time = timezone.now()
        now_time_str = now_time.strftime("%d")
        # order = OrderInfo.objects.filter(Q(sp2=num) & Q(order_status=2) & Q(create_time__day=now_time_str)).aggregate(nums=Count('sp2'))
        # t = order['nums']
        count = 1
        order1 = OrderInfo.objects.filter(Q(sp2=num) & Q(order_status=2) & Q(create_time__day=now_time_str))
        for order2 in order1:
            # print(type(order2.sp2))
            if count <= 4:
                count = count + 1
            else:
                h = int(order2.sp2)
                if h == 2:
                    h = 0
                else:
                    h = h + 1
                order2.sp2 = str(h)
                order2.save()

        # 遍历获取订单商品的信息
        for order in orders:
            # 根据order_id查询订单商品的信息
            order_skus = OrderGoods.objects.filter(order_id=order.id)
            order_addr = OrderInfo.objects.filter(order_id=order.order_id)
            order_address = order_addr[0].address_id
            address = Address.objects.filter(id=order_address)
            # 遍历order_skus计算商品的小计
            for order_sku in order_skus:
                # 计算小计1
                amount = order_sku.count * order_sku.price
                # 动态给order_sku增加属性amount保存订单商品的小计
                order_sku.amount = amount
            # 动态给order增加属性，保存订单商品的信息
            order.order_skus = order_skus
            order.status_name = OrderInfo.ORDER_STATUS[str(order.order_status)]
            order.deliver_name = OrderInfo.DELIVER_STATUS[str(order.deliver_status)]
        # 分页
        paginator = Paginator(orders, 10)

        # 处理页码
        # 获取第page页的内容
        try:
            page = int(page)
        except Exception as e:
            page = 1
        if page > paginator.num_pages:
            page = 1
        # 获取第page页的Page实例对象
        order_page = paginator.page(page)
        # print(type(order_page))
        # todo：进行页码的控制，页面上最多显示5个页码，总页数如果小于5页，页面上显示所有页码，如果当前页是前3页，显示1-5页，如果当前页是后3页，显示后5页，如果是其他情况，显示当前页的前2页，当前页，当前页的后2页
        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1, num_pages + 1)

        elif page <= 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            pages = range(num_pages - 4, num_pages + 1)
        else:
            pages = range(page - 2, page + 3)

        # 组织上下文
        context = {
            # 'order1': order1,
            # 'order2': order2,
            'name': name,
            'mobile': mobile,
            'order_page': order_page,
            'pages': pages,
            'page': 'order',
            'address': address,
        }

        # 使用模板
        return render(request, 'deliver_center_order.html', context)

class OrderInfo1View(LoginRequiredMixin, View):
    def get(self, request, page=None):
        is_login = request.session.get('IS_LOGIN', False)
        if is_login:
            name = request.session.get('name')
            mobile = request.session.get('mobile')

        num = int(name)
        orders = OrderInfo.objects.filter(Q(sp2=num) & Q(order_status= 2)).order_by('order_id')

        now_time = timezone.now()
        now_time_str1 = now_time.strftime("%Y")
        now_time_str2 = now_time.strftime("%m")
        now_time_str3 = now_time.strftime("%d")
        a = int(now_time_str1)
        b = int(now_time_str2)
        c = int(now_time_str3) + 1
        m_start = datetime.datetime(a, b, c, 7, 0, 0)
        m_end = datetime.datetime(a, b, c, 12, 0, 0)
        a_start = datetime.datetime(a, b, c, 13, 0, 0)
        a_end = datetime.datetime(a, b, c, 19, 0, 0)
        order1 = orders.filter(Q(choose_time__gte=m_start) & Q(choose_time__lte=m_end))
        order2 = orders.filter(Q(choose_time__gte=a_start) & Q(choose_time__lte=a_end))
        # 遍历获取订单商品的信息
        for order in order1:
            # 根据order_id查询订单商品的信息
            order_skus = OrderGoods.objects.filter(order_id=order.id)
            order_addr = OrderInfo.objects.filter(order_id=order.order_id)
            order_address = order_addr[0].address_id
            address = Address.objects.filter(id=order_address)
            # 遍历order_skus计算商品的小计
            for order_sku in order_skus:
                # 计算小计1
                amount = order_sku.count * order_sku.price
                # 动态给order_sku增加属性amount保存订单商品的小计
                order_sku.amount = amount
            # 动态给order增加属性，保存订单商品的信息
            order.order_skus = order_skus
            order.status_name = OrderInfo.ORDER_STATUS[str(order.order_status)]
            order.deliver_name = OrderInfo.DELIVER_STATUS[str(order.deliver_status)]

        for order in order2:
            # 根据order_id查询订单商品的信息
            order_skus = OrderGoods.objects.filter(order_id=order.id)
            order_addr = OrderInfo.objects.filter(order_id=order.order_id)
            order_address = order_addr[0].address_id
            address = Address.objects.filter(id=order_address)
            # 遍历order_skus计算商品的小计
            for order_sku in order_skus:
                # 计算小计1
                amount = order_sku.count * order_sku.price
                # 动态给order_sku增加属性amount保存订单商品的小计
                order_sku.amount = amount
            # 动态给order增加属性，保存订单商品的信息
            order.order_skus = order_skus
            order.status_name = OrderInfo.ORDER_STATUS[str(order.order_status)]
            order.deliver_name = OrderInfo.DELIVER_STATUS[str(order.deliver_status)]
        # # 分页
        # paginator = Paginator(orders, 10)
        #
        # # 处理页码
        # # 获取第page页的内容
        # try:
        #     page = int(page)
        # except Exception as e:
        #     page = 1
        # if page > paginator.num_pages:
        #     page = 1
        # # 获取第page页的Page实例对象
        # order_page = paginator.page(page)
        # # print(type(order_page))
        # # todo：进行页码的控制，页面上最多显示5个页码，总页数如果小于5页，页面上显示所有页码，如果当前页是前3页，显示1-5页，如果当前页是后3页，显示后5页，如果是其他情况，显示当前页的前2页，当前页，当前页的后2页
        # num_pages = paginator.num_pages
        # if num_pages < 5:
        #     pages = range(1, num_pages + 1)
        #
        # elif page <= 3:
        #     pages = range(1, 6)
        # elif num_pages - page <= 2:
        #     pages = range(num_pages - 4, num_pages + 1)
        # else:
        #     pages = range(page - 2, page + 3)

        # 组织上下文
        context = {
            'order1': order1,
            'order2': order2,
            'name': name,
            'mobile': mobile,
            # 'order_page': order_page,
            # 'pages': pages,
            # 'page': 'order',
            # 'address': address,
        }

        # 使用模板
        return render(request, 'deliver_center_order1.html', context)

class DeliverStatusView(LoginRequiredMixin, View):

    def get(self, request, order_id, page=None):
        orders = OrderInfo.objects.filter(order_id=order_id)
        for order1 in orders:
            order1.deliver_status = 2
            now_time = timezone.now()
            now_hour = int(now_time.strftime("%H"))
            now_min = int(now_time.strftime("%M"))
            ch_hour = int(order1.choose_time.strftime("%H"))
            ch_min = int(order1.choose_time.strftime("%M"))
            if ch_hour-1 <= now_hour <= ch_hour:
                if now_min <= ch_min:
                    order1.sp3 = 1
            else:
                order1.sp3 = 0
            order1.save()

        is_login = request.session.get('IS_LOGIN', False)
        if is_login:
            name = request.session.get('name')
            mobile = request.session.get('mobile')

        num = int(name)
        orders = OrderInfo.objects.filter(sp2=num).order_by('order_id')
        now_time = timezone.now()
        now_time_str1 = now_time.strftime("%Y")
        now_time_str2 = now_time.strftime("%m")
        now_time_str3 = now_time.strftime("%d")
        a = int(now_time_str1)
        b = int(now_time_str2)
        c = int(now_time_str3) + 1
        m_start = datetime.datetime(a, b, c, 7, 0, 0)
        m_end = datetime.datetime(a, b, c, 12, 0, 0)
        a_start = datetime.datetime(a, b, c, 13, 0, 0)
        a_end = datetime.datetime(a, b, c, 19, 0, 0)
        order1 = orders.filter(Q(choose_time__gte=m_start) & Q(choose_time__lte=m_end))
        order2 = orders.filter(Q(choose_time__gte=a_start) & Q(choose_time__lte=a_end))
        # 遍历获取订单商品的信息
        for order in order1:
            # 根据order_id查询订单商品的信息
            order_skus = OrderGoods.objects.filter(order_id=order.id)
            order_addr = OrderInfo.objects.filter(order_id=order.order_id)
            order_address = order_addr[0].address_id
            address = Address.objects.filter(id=order_address)
            # 遍历order_skus计算商品的小计
            for order_sku in order_skus:
                # 计算小计1
                amount = order_sku.count * order_sku.price
                # 动态给order_sku增加属性amount保存订单商品的小计
                order_sku.amount = amount
            # 动态给order增加属性，保存订单商品的信息
            order.order_skus = order_skus
            order.status_name = OrderInfo.ORDER_STATUS[str(order.order_status)]
            order.deliver_name = OrderInfo.DELIVER_STATUS[str(order.deliver_status)]

        for order in order2:
            # 根据order_id查询订单商品的信息
            order_skus = OrderGoods.objects.filter(order_id=order.id)
            order_addr = OrderInfo.objects.filter(order_id=order.order_id)
            order_address = order_addr[0].address_id
            address = Address.objects.filter(id=order_address)
            # 遍历order_skus计算商品的小计
            for order_sku in order_skus:
                # 计算小计1
                amount = order_sku.count * order_sku.price
                # 动态给order_sku增加属性amount保存订单商品的小计
                order_sku.amount = amount
            # 动态给order增加属性，保存订单商品的信息
            order.order_skus = order_skus
            order.status_name = OrderInfo.ORDER_STATUS[str(order.order_status)]
            order.deliver_name = OrderInfo.DELIVER_STATUS[str(order.deliver_status)]
        # # 分页
        # paginator = Paginator(orders, 10)
        #
        # # 处理页码
        # # 获取第page页的内容
        # try:
        #     page = int(page)
        # except Exception as e:
        #     page = 1
        # if page > paginator.num_pages:
        #     page = 1
        # # 获取第page页的Page实例对象
        # order_page = paginator.page(page)
        # # print(type(order_page))
        # # todo：进行页码的控制，页面上最多显示5个页码，总页数如果小于5页，页面上显示所有页码，如果当前页是前3页，显示1-5页，如果当前页是后3页，显示后5页，如果是其他情况，显示当前页的前2页，当前页，当前页的后2页
        # num_pages = paginator.num_pages
        # if num_pages < 5:
        #     pages = range(1, num_pages + 1)
        #
        # elif page <= 3:
        #     pages = range(1, 6)
        # elif num_pages - page <= 2:
        #     pages = range(num_pages - 4, num_pages + 1)
        # else:
        #     pages = range(page - 2, page + 3)

        # 组织上下文
        context = {
            'order1': order1,
            'order2': order2,
            'name': name,
            'mobile': mobile,
            # 'order_page': order_page,
            # 'pages': pages,
            # 'page': 'order',
            'address': address,
        }
        # 使用模板
        return render(request, 'deliver_center_order1.html', context)


class MMapView(LoginRequiredMixin, View):

    def get(self, request):
        is_login = request.session.get('IS_LOGIN', False)
        if is_login:
            name = request.session.get('name')
            mobile = request.session.get('mobile')

        num = int(name)
        orders = OrderInfo.objects.filter(Q(sp2=num) & Q(order_status=2)).order_by('order_id')
        now_time = timezone.now()
        now_time_str1 = now_time.strftime("%Y")
        now_time_str2 = now_time.strftime("%m")
        now_time_str3 = now_time.strftime("%d")
        a = int(now_time_str1)
        b = int(now_time_str2)
        c = int(now_time_str3) + 1
        m_start = datetime.datetime(a, b, c, 7, 0, 0)
        m_end = datetime.datetime(a, b, c, 12, 0, 0)
        # a_start = datetime.datetime(a, b, c, 13, 0, 0)
        # a_end = datetime.datetime(a, b, c, 19, 0, 0)
        order1 = orders.filter(Q(choose_time__gte=m_start) & Q(choose_time__lte=m_end))
        # order2 = orders.filter(Q(choose_time__gte=a_start) & Q(choose_time__lte=a_end))
        for order in order1:
            order.order_status = 3
            order.save()

        context = {
            'order1': order1
        }
        # print(context)
        return render(request, 'zmap.html', context)

class AMapView(LoginRequiredMixin, View):

    def get(self, request):
        is_login = request.session.get('IS_LOGIN', False)
        if is_login:
            name = request.session.get('name')
            mobile = request.session.get('mobile')

        num = int(name)
        orders = OrderInfo.objects.filter(Q(sp2=num) & Q(order_status=2)).order_by('order_id')
        now_time = timezone.now()
        now_time_str1 = now_time.strftime("%Y")
        now_time_str2 = now_time.strftime("%m")
        now_time_str3 = now_time.strftime("%d")
        a = int(now_time_str1)
        b = int(now_time_str2)
        c = int(now_time_str3) + 1
        # m_start = datetime.datetime(a, b, c, 7, 0, 0)
        # m_end = datetime.datetime(a, b, c, 12, 0, 0)
        a_start = datetime.datetime(a, b, c, 13, 0, 0)
        a_end = datetime.datetime(a, b, c, 19, 0, 0)
        # order1 = orders.filter(Q(choose_time__gte=m_start) & Q(choose_time__lte=m_end))
        order2 = orders.filter(Q(choose_time__gte=a_start) & Q(choose_time__lte=a_end))
        for order in order2:
            order.order_status = 3
            order.save()

        context = {
            'order2': order2
        }
        # print(context)
        return render(request, 'amap.html', context)

class DeliverMapView(LoginRequiredMixin, View):
    "订单配送"

    def get(self, request, order_id):
        orders = OrderInfo.objects.filter(order_id=order_id)
        for order in orders:
            #配送时间条件必写
            # order_id = OrderInfo.objects.filter(order_id=order.order_id)
            # print(order_id[0].order_id)
            # now_time = timezone.now()
            # now_time_str = now_time.strftime("%d")
            # now_day = int(now_time_str)
            # choose_day = int(order.choose_time.strftime("%d"))
            # if choose_day == now_day:
                order1 = Address.objects.get(id=order.address_id)
                order.order_status = 3
                # # order.deliver_status = 2
                order.save()
        context = {
            'order1': order1
        }
        return render(request, 'map.html', context)