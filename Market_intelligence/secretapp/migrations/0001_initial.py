# Generated by Django 5.0.7 on 2024-07-30 18:36

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Secret',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=300)),
                ('passphrase', models.CharField(max_length=100)),
                ('secret_key', models.CharField(max_length=300)),
            ],
            options={
                'ordering': ['pk'],
            },
        ),
    ]
