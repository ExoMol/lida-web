# Generated by Django 3.2.12 on 2022-02-02 15:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_site', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='isotopologue',
            name='vib_quantum_labels',
            field=models.CharField(default='', max_length=64),
        ),
        migrations.AddField(
            model_name='isotopologue',
            name='vib_quantum_labels_html',
            field=models.CharField(default='', max_length=128),
        ),
    ]
