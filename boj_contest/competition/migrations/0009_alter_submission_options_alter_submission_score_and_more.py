# Generated by Django 5.1 on 2024-11-23 10:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competition', '0008_submission_is_correct'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='submission',
            options={'ordering': ['-submission_time']},
        ),
        migrations.AlterField(
            model_name='submission',
            name='score',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='submission',
            name='submission_time',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterUniqueTogether(
            name='submission',
            unique_together={('user_id', 'problem_id')},
        ),
    ]
