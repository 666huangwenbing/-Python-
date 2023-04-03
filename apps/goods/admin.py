from django.contrib import admin
from apps.goods.models import GoodsType,GoodsSKU,GoodsSPU,GoodsImage
# # Register your models here.
admin.site.register([GoodsType,GoodsSKU,GoodsSPU,GoodsImage])