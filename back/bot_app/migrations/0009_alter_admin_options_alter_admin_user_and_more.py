# Generated by Django 5.0.2 on 2024-05-04 03:56

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot_app', '0008_alter_admin_user_selectedadmin'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='admin',
            options={},
        ),
        migrations.AlterField(
            model_name='admin',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='admin', to='bot_app.user'),
        ),
        migrations.DeleteModel(
            name='SelectedAdmin',
        ),
    ]
