# Generated by Django 3.2.8 on 2021-10-26 11:12

from django.db import migrations, models
import django.db.models.deletion
import elida.apps.mixins


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('molecule', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='State',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lifetime', models.FloatField(null=True)),
                ('energy', models.FloatField()),
                ('el_state_str', models.CharField(max_length=64)),
                ('vib_state_str', models.CharField(max_length=64)),
                ('el_state_html', models.CharField(max_length=64)),
                ('vib_state_html', models.CharField(max_length=64)),
                ('vib_state_html_alt', models.CharField(max_length=128)),
                ('isotopologue', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='molecule.isotopologue')),
            ],
            bases=(elida.apps.mixins.ModelMixin, models.Model),
        ),
    ]
