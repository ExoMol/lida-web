# Generated by Django 3.2.12 on 2022-02-03 16:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Isotopologue",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("time_added", models.DateTimeField(auto_now_add=True)),
                ("time_modified", models.DateTimeField(auto_now=True)),
                ("iso_formula_str", models.CharField(max_length=32)),
                ("dataset_name", models.CharField(max_length=16)),
                ("version", models.PositiveIntegerField()),
                (
                    "ground_el_state_str",
                    models.CharField(blank=True, default="", max_length=64),
                ),
                ("vib_quantum_labels", models.CharField(default="", max_length=64)),
                (
                    "vib_quantum_labels_html",
                    models.CharField(default="", max_length=128),
                ),
                ("vib_state_dim", models.PositiveSmallIntegerField(default=0)),
                ("iso_slug", models.CharField(max_length=32)),
                ("html", models.CharField(max_length=64)),
                ("mass", models.FloatField()),
                ("number_states", models.PositiveIntegerField()),
                ("number_transitions", models.PositiveIntegerField()),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Molecule",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("time_added", models.DateTimeField(auto_now_add=True)),
                ("time_modified", models.DateTimeField(auto_now=True)),
                ("formula_str", models.CharField(max_length=16)),
                ("name", models.CharField(default="", max_length=64)),
                ("slug", models.CharField(max_length=16)),
                ("html", models.CharField(max_length=64)),
                ("charge", models.SmallIntegerField()),
                ("number_atoms", models.PositiveSmallIntegerField()),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="State",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("time_added", models.DateTimeField(auto_now_add=True)),
                ("time_modified", models.DateTimeField(auto_now=True)),
                ("lifetime", models.FloatField(null=True)),
                ("energy", models.FloatField()),
                ("el_state_str", models.CharField(max_length=64)),
                ("vib_state_str", models.CharField(max_length=64)),
                ("el_state_html", models.CharField(max_length=64)),
                ("el_state_html_notags", models.CharField(max_length=64)),
                ("vib_state_html", models.CharField(max_length=64)),
                ("vib_state_html_notags", models.CharField(max_length=64)),
                ("vib_state_sort_key", models.CharField(max_length=64)),
                ("state_html", models.CharField(max_length=128)),
                ("state_html_notags", models.CharField(max_length=128)),
                ("state_sort_key", models.CharField(max_length=128)),
                ("number_transitions_from", models.PositiveIntegerField()),
                ("number_transitions_to", models.PositiveIntegerField()),
                (
                    "isotopologue",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="app_site.isotopologue",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Transition",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("time_added", models.DateTimeField(auto_now_add=True)),
                ("time_modified", models.DateTimeField(auto_now=True)),
                ("partial_lifetime", models.FloatField()),
                ("branching_ratio", models.FloatField()),
                ("delta_energy", models.FloatField()),
                (
                    "final_state",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="transition_to_set",
                        to="app_site.state",
                    ),
                ),
                (
                    "initial_state",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="transition_from_set",
                        to="app_site.state",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.AddField(
            model_name="isotopologue",
            name="molecule",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE, to="app_site.molecule"
            ),
        ),
    ]
