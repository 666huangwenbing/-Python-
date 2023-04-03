from django.db import models
from db.base_model import BaseModel



class Deliver(BaseModel):
    # deliver_id = models.CharField(max_length=20, primary_key=True, verbose_name='配送员编号')
    name = models.CharField(max_length=20, verbose_name='配送员姓名')
    password = models.CharField(max_length=20,verbose_name='密码')
    mobile = models.CharField(max_length=11, unique=True, verbose_name='手机号')

    class Meta:
        db_table = 'df_deliver'
        verbose_name = '配送员'
        verbose_name_plural = verbose_name
