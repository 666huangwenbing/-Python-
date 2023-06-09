from django.db.models import Q, Count
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import View

from apps.deliver.models import Deliver
from apps.goods.models import GoodsSKU
from django_redis import get_redis_connection
from apps.user.models import Address
from utils.mixin import LoginRequiredMixin
from django.http import JsonResponse
from apps.order.models import OrderInfo, OrderGoods
from datetime import datetime
from django.db import transaction
from alipay import AliPay
from django.conf import settings
import os


# Create your views here.
# class ChoosetimeView(LoginRequiredMixin, View):
#     def post(self,request):
#         choose_time = request.POST.get('choosetime')
#         print(choose_time)
#         return render(request, 'choose.html')
#         # return redirect(reverse('order:place'))

class OrderPlaceView(LoginRequiredMixin, View):
    '''提交订单页面显示'''

    def post(self, request):
        '''提交订单页面显示'''
        # 获取登录的用户
        # now_time = timezone.now()
        # now_time_str = now_time.strftime("%H")
        # now_hour = int(now_time_str)
        # if now_hour < 17:
        user = request.user
        # 获取参数:sku_ids
        sku_ids = request.POST.getlist('sku_ids')
        # 校验参数
        if not sku_ids:
            # 跳转到购物车页面
            return redirect(reverse('cart:show'))

        coon = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        skus = []
        # 保存商品的总件数和总价格
        total_count = 0
        total_price = 0
        # 遍历sku_ids获取用户要购买的商品的信息
        for sku_id in sku_ids:
            # 根据商品的id获取商品的信息
            sku = GoodsSKU.objects.get(id=sku_id)
            # 获取用户所要购买的商品的数量
            count = coon.hget(cart_key, sku_id)
            # 给数目解码
            count = count.decode()
            # 计算商品的小计
            amount = sku.price * int(count)
            # 动态给sku增加属性count、amount，保存购买商品的数量和总价格
            sku.count = count
            sku.amount = amount
            # 追加
            skus.append(sku)
            # 累加计算商品的总件数和总价格
            total_count += int(count)
            total_price += amount
        # 运费:实际开发的时候，属于一个子系统
        transit_price = 10  # 写死
        # 实付款
        total_pay = total_price + transit_price

        # 获取用户的收件地址
        addrs = Address.objects.filter(user=user)

        # 组织上下文
        sku_ids = ','.join(sku_ids)
        context = {
            'skus': skus,
            'total_count': total_count,
            'total_price': total_price,
            'transit_price': transit_price,
            'total_pay': total_pay,
            'addrs': addrs,
            'sku_ids': sku_ids,
        }

        # 使用模板
        return render(request, 'place_order.html', context)


class OrderCommitView(View):
    '''订单创建'''
    @transaction.atomic
    def post(self, request):
        '''订单创建'''
        # 判断用户是否登录
        now_time = timezone.now()
        now_time_str = now_time.strftime("%H")
        now_time_str2 = now_time.strftime("%m")
        now_time_str3 = now_time.strftime("%d")
        now_day = int(now_time_str3)
        now_hour = int(now_time_str)
        order3 = OrderInfo.objects.filter(Q(create_time__month=now_time_str2) & Q(create_time__day=now_time_str3)).aggregate(nums=Count('create_time__day'))
        t = order3['nums']
        if t <= 12:
            # if now_hour < 17:
                user = request.user
                if not user.is_authenticated:
                    # 用户未登录
                    return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

                # 接收参数
                addr_id = request.POST.get('addr_id')
                pay_method = request.POST.get('pay_method')
                sku_ids = request.POST.get('sku_ids')
                choose_time = request.POST.get('choosetime')
                choose_time = datetime.strptime(choose_time, '%Y-%m-%dT%H:%M')
                choose = choose_time.strftime("%d")
                choose1 = choose_time.strftime("%H")
                choose_day = int(choose)
                choose_hour = int(choose1)
                if choose_day == now_day + 1 and 7 <= choose_hour < 12 or 13 < choose_hour <= 19:
                    # 校验参数
                    if not all([addr_id, pay_method, sku_ids, choose_time]):
                        return JsonResponse({'res': 1, 'errmsg': '参数不完整'})
                    # 校验支付方式
                    if pay_method not in OrderInfo.PAY_METHOD.keys():
                        return JsonResponse({'res': 2, 'errmsg': '非法的支付方式'})
                    # 校验地址
                    try:
                        addr = Address.objects.get(id=addr_id)
                    except Address.DoesNotExist:
                        # 地址不存在
                        return JsonResponse({'res': 3, 'errmsg': '地址非法'})

                    # todo:创建订单核心业务
                    # 组织参数
                    # 订单id:20171122181630+用户id
                    order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(1)
                    orders = OrderInfo.objects.filter()
                    for order in orders:
                        if order.id:
                            order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(order.id)
                            sp1 = user.id
                            sp2 = sp1 % 3
                            # sp1 = order_id[-2:]
                    # 运费
                    transit_price = 10
                    # 总数目和总金额
                    total_count = 0
                    total_price = 0

                    # 设置事务保存点
                    save_id = transaction.savepoint()

                    try:
                        # todo:向df_order_info表中添加一条记录
                        order = OrderInfo.objects.create(order_id=order_id,
                                                         user=user,
                                                         address=addr,
                                                         pay_method=pay_method,
                                                         total_count=total_count,
                                                         total_price=total_price,
                                                         transit_price=transit_price,
                                                         choose_time=choose_time,
                                                         sp1=sp1,
                                                         sp2=sp2)

                        # todo: 用户的订单中有几个商品，需要向df_order_goods表中加入几条记录
                        coon = get_redis_connection('default')
                        cart_key = 'cart_%d' % user.id
                        sku_ids = sku_ids.split(',')
                        for sku_id in sku_ids:
                            # 获取商品的信息
                            try:
                                # select * from df_goods_sku where id=sku_id for update
                                sku = GoodsSKU.objects.select_for_update().get(id=sku_id)
                            except:
                                # 商品不存在
                                transaction.savepoint_rollback(save_id)
                                return JsonResponse({'res': 4, 'errmsg': '商品不存在'})
                            # 从redis中获取用户所要购买的商品的数量
                            count = coon.hget(cart_key, sku_id)

                            # todo：判断商品的库存
                            if int(count) > sku.stock:
                                transaction.savepoint_rollback(save_id)
                                return JsonResponse({'res': 6, 'errmsg': '商品库存不足'})

                            # todo: 向df_order_goods表添加一条记录
                            OrderGoods.objects.create(order=order,
                                                      sku=sku,
                                                      count=count,
                                                      price=sku.price)

                            # todo: 更新商品的库存和销量
                            sku.stock -= int(count)
                            sku.sales += int(count)
                            sku.save()

                            # todo: 累加计算订单商品的总数量和总价格
                            amount = sku.price * int(count)
                            total_count += int(count)
                            total_price += amount

                        # todo: 更新订单信息表中的商品总数量和总价格
                        order.total_count = total_count
                        order.total_price = total_price
                        order.save()
                    except Exception as e:
                        transaction.savepoint_rollback(save_id)
                        return JsonResponse({'res': 7, 'errmsg': '下单失败'})

                    # 提交事务
                    transaction.savepoint_commit(save_id)

                    # todo: 清除用户购物车中对应的记录
                    coon.hdel(cart_key, *sku_ids)

                    # 返回应答
                    return JsonResponse({'res': 5, 'message': '创建成功'})
                else:
                    return JsonResponse({'res': 10, 'errmsg': '选择订单到达时间错误'})
            # else:
            #     return JsonResponse({'res': 8, 'errmsg': '非下单时间'})
        else:
            return JsonResponse({'res': 9, 'errmsg': '下单数量已达上限，请明天下单'})

class OrderPayView(View):
    '''订单支付'''

    def post(self, request):
        '''订单支付'''
        # 用户是否登录
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

        # 接收参数
        order_id = request.POST.get('order_id')

        # 校验参数
        if not order_id:
            return JsonResponse({'res': 1, 'errmsg': '无效的订单id'})
        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user, pay_method=3, order_status=1)
        except OrderInfo.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '订单错误'})

        # 业务处理：使用python sdk调用支付宝的支付接口
        # 初始化
        alipay = AliPay(
            appid="2021000119665797",  # 支付宝分配给开发者的应用ID
            app_notify_url=None,  # 默认回调url
            app_private_key_path=os.path.join(settings.BASE_DIR, 'apps/order/app_private_key.pem'),
            alipay_public_key_path=os.path.join(settings.BASE_DIR, 'apps/order/alipay_public_key.pem'),
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=True  # 默认False
        )
        # 调用支付接口
        # 电脑网站支付，需要跳转到https://openapi.alipay.com/gateway.do? + order_string
        total_pay = order.total_price + order.transit_price
        #统一收单下单并支付页面接口
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,  # 订单id
            total_amount=str(total_pay),  # 支付总金额
            subject='天天生鲜%s' % order_id,
            return_url=None,
            notify_url=None  # 可选, 不填则使用默认notify url
        )

        # 返回应答
        pay_url = 'https://openapi.alipaydev.com/gateway.do?' + order_string
        return JsonResponse({'res': 3, 'pay_url': pay_url})


class CheckPayView(View):
    '''查看订单支付的结果'''

    def post(self, request):
        '''查询支付结果'''
        # 用户是否登录
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

        # 接收参数
        order_id = request.POST.get('order_id')

        # 校验参数
        if not order_id:
            return JsonResponse({'res': 1, 'errmsg': '无效的订单id'})
        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user, pay_method=3, order_status=1)
        except OrderInfo.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '订单错误'})

        # 业务处理：使用python sdk调用支付宝的支付接口
        # 初始化
        alipay = AliPay(
            appid="2021000119665797",  # 应用id
            app_notify_url=None,  # 默认回调url
            app_private_key_path=os.path.join(settings.BASE_DIR, 'apps/order/app_private_key.pem'),
            alipay_public_key_path=os.path.join(settings.BASE_DIR, 'apps/order/alipay_public_key.pem'),
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=True  # 默认False
        )

        # 调用支付宝的交易查询接口
        while True:
            response = alipay.api_alipay_trade_query(order_id)
            code = response.get('code')
            if code == '10000' and response.get('trade_status') == 'TRADE_SUCCESS':
                # 支付成功
                # 获取支付宝交易号
                trade_no = response.get('trade_no')

                # 更新订单的状态
                order.order_status = 2  # 待发货
                order.save()

                # 返回结果
                return JsonResponse({'res': 3, 'errmsg': '支付成功'})

            elif code == '40004' or (code == '10000' and response.get('trade_status') == 'WAIT_BUYER_PAY'):
                # 等待买家付款
                # 业务处理失败，
                import time
                time.sleep(5)
                continue
            else:
                # 支付出错
                return JsonResponse({'res': 4, 'errmsg': '支付失败'})


class CommentView(LoginRequiredMixin, View):
    """订单评论"""

    def get(self, request, order_id):
        """提供订单评论页面"""
        user = request.user

        # 校验参数
        if not order_id:
            return redirect(reverse('user:order'))

        try:
            order = OrderInfo.objects.get(order_id=order_id,
                                          user=user,
                                          )
        except OrderInfo.DoesNotExist:
            return redirect(reverse('user:order'))

        order.status_name = OrderInfo.ORDER_STATUS[str(order.order_status)]

        # 获取订单的商品信息
        order_skus = OrderGoods.objects.filter(order=order)
        for order_sku in order_skus:
            # 计算商品小计
            amount = order_sku.price * order_sku.count
            order_sku.amount = amount

        order.order_skus = order_skus

        return render(request, 'order_comment.html', {'order': order})

    def post(self, request, order_id):
        """处理评论内容"""
        user = request.user

        # 校验参数
        if not order_id:
            return redirect(reverse('user:order'))

        try:
            order = OrderInfo.objects.get(order_id=order_id,
                                          user=user,
                                          )
        except OrderInfo.DoesNotExist:
            return redirect(reverse('user:order'))

        # 获取评论条数
        total_count = request.POST.get('total_count')
        total_count = int(total_count)

        for i in range(1, total_count + 1):
            # 获取评论的商品的id
            sku_id = request.POST.get('sku_{0}'.format(i))

            # 获取评论内容
            content = request.POST.get('content_{0}'.format(i))

            try:
                order_goods = OrderGoods.objects.get(order=order, sku_id=sku_id)
            except OrderGoods.DoesNotExist:
                continue

            order_goods.comment = content
            order_goods.save()

        order.order_status = 5
        order.save()

        return redirect(reverse('user:order', kwargs={'page': 1}))
