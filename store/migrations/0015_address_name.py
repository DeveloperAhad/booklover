# Generated by Django 3.2.4 on 2021-06-30 14:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0014_auto_20210630_1921'),
    ]

    operations = [
        migrations.AddField(
            model_name='address',
            name='name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]