# Generated by Django 3.2.20 on 2023-07-05 17:18

from django.db import migrations, models
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0038_auto_20230703_1857'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='order',
            name='foodcartapp_last_na_4dac90_idx',
        ),
        migrations.RenameField(
            model_name='order',
            old_name='first_name',
            new_name='firstname',
        ),
        migrations.RenameField(
            model_name='order',
            old_name='last_name',
            new_name='lastname',
        ),
        migrations.RemoveField(
            model_name='order',
            name='phone_number',
        ),
        migrations.AddField(
            model_name='order',
            name='phonenumber',
            field=phonenumber_field.modelfields.PhoneNumberField(blank=True, max_length=128, null=True, region='RU'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['lastname', 'firstname', 'phonenumber'], name='foodcartapp_lastnam_ae467d_idx'),
        ),
    ]
