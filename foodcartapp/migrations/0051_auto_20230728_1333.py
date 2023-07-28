# Generated by Django 3.2.20 on 2023-07-28 10:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0050_alter_order_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='restaurant',
            name='lat',
            field=models.FloatField(blank=True, null=True, verbose_name='Координаты ресторана: широта (latitude)'),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='lon',
            field=models.FloatField(blank=True, null=True, verbose_name='Координаты ресторана: долгота (longitude)'),
        ),
        migrations.AlterField(
            model_name='order',
            name='restaurant',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='orders', to='foodcartapp.restaurant', verbose_name='Ресторан - исполнитель заказа'),
        ),
    ]
