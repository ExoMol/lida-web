# Generated by Django 3.2.8 on 2021-10-12 13:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lifetimes', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='state',
            name='state_html',
            field=models.CharField(max_length=128),
        ),
    ]
