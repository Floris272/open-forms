# Generated by Django 2.2.24 on 2021-11-17 16:29

from django.db import migrations, models

import openforms.template.validators


class Migration(migrations.Migration):

    dependencies = [
        ("emails", "0005_auto_20211117_1658"),
    ]

    operations = [
        migrations.AlterField(
            model_name="confirmationemailtemplate",
            name="subject",
            field=models.CharField(
                blank=True,
                help_text="Subject of the email message",
                max_length=1000,
                validators=[openforms.template.validators.DjangoTemplateValidator()],
                verbose_name="subject",
            ),
        ),
    ]
