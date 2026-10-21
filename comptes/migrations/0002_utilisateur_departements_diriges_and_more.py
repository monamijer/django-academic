
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("academique", "0005_cours_niveau"),
        ("comptes", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AddField(
                    model_name="utilisateur",
                    name="departements_diriges",
                    field=models.ManyToManyField(
                        blank=True,
                        help_text="Départements dirigés (Chef de département).",
                        related_name="chefs",
                        to="academique.departement",
                        verbose_name="Départements dirigés",
                    ),
                ),
                migrations.AddField(
                    model_name="utilisateur",
                    name="departements_enseignes",
                    field=models.ManyToManyField(
                        blank=True,
                        help_text="Départements dans lesquels le professeur enseigne.",
                        related_name="enseignants",
                        to="academique.departement",
                        verbose_name="Départements d'enseignement",
                    ),
                ),
                migrations.AddField(
                    model_name="utilisateur",
                    name="facultes_gerees",
                    field=models.ManyToManyField(
                        blank=True,
                        help_text="Facultés supervisées (Doyen).",
                        related_name="utilisateurs_gerants",
                        to="academique.faculte",
                        verbose_name="Facultés gérées",
                    ),
                ),
                migrations.AlterField(
                    model_name="utilisateur",
                    name="departement",
                    field=models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="membres",
                        to="academique.departement",
                    ),
                ),
                migrations.AlterField(
                    model_name="utilisateur",
                    name="faculte",
                    field=models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="doyens",
                        to="academique.faculte",
                    ),
                ),
            ],
        ),
    ]

