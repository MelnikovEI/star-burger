# Generated by Django 3.2.20 on 2023-07-25 17:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0045_auto_20230725_2025'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='comment',
            field=models.TextField(blank=True, max_length=500, verbose_name='Комментарий'),
        ),
    ]
