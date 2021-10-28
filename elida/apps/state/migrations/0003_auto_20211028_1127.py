# Generated by Django 3.2.8 on 2021-10-28 11:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('state', '0002_state_html'),
    ]

    operations = [
        migrations.AddField(
            model_name='state',
            name='number_transitions_from',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='state',
            name='number_transitions_to',
            field=models.PositiveIntegerField(default=0),
        ),
    ]