# Generated by Django 5.0.1 on 2024-03-22 16:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authors', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='author',
            name='host',
            field=models.URLField(blank=True, default='https://nexapulse-25959148b934.herokuapp.com/', null=True),
        ),
    ]
