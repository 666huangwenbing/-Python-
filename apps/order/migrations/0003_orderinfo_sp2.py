# Generated by Django 3.2 on 2022-05-22 22:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderinfo',
            name='sp2',
            field=models.CharField(max_length=11, null=True, verbose_name='标识'),
        ),
    ]
