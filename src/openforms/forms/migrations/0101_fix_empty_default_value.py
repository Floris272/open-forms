# Generated by Django 4.2.16 on 2024-10-07 14:36

from django.db import migrations

from openforms.forms.migration_operations import ConvertComponentsOperation


class Migration(migrations.Migration):

    dependencies = [
        ("forms", "0100_merge_20240920_1816"),
    ]

    operations = [
        ConvertComponentsOperation("textfield", "fix_empty_default_value"),
        ConvertComponentsOperation("email", "fix_empty_default_value")
    ]
