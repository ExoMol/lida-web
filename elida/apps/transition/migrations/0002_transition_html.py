# Generated by Django 3.2.8 on 2021-10-28 12:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transition', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='transition',
            name='html',
            field=models.CharField(default='', max_length=256),
            preserve_default=False,
        ),
    ]
