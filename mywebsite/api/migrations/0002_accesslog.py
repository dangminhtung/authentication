# Generated by Django 4.2.15 on 2024-10-16 17:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AccessLog',
            fields=[
                ('id_AL', models.BigAutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('dob', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(max_length=255)),
                ('id_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.userinfo')),
            ],
        ),
    ]