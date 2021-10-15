# Generated by Django 3.2.8 on 2021-10-15 13:57

from django.db import migrations, models
import django.db.models.deletion
import elida.apps.mixins


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('state', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Transition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('partial_lifetime', models.FloatField()),
                ('branching_ratio', models.FloatField()),
                ('d_energy', models.FloatField()),
                ('final_state', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transition_to_set', to='state.state')),
                ('initial_state', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transition_from_set', to='state.state')),
            ],
            bases=(elida.apps.mixins.ModelMixin, models.Model),
        ),
    ]