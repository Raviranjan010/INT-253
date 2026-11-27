import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('community', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.AddField(model_name='discussionthread', name='is_hidden', field=models.BooleanField(default=False)),
        migrations.AddField(model_name='discussionreply', name='is_hidden', field=models.BooleanField(default=False)),
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reason', models.CharField(max_length=500)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('reply', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='community.discussionreply')),
                ('reporter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('thread', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reports', to='community.discussionthread')),
            ],
            options={'constraints': [
                models.UniqueConstraint(fields=('reporter', 'thread'), condition=models.Q(reply__isnull=True), name='one_thread_report_per_user'),
                models.UniqueConstraint(fields=('reporter', 'reply'), condition=models.Q(reply__isnull=False), name='one_reply_report_per_user'),
            ]},
        ),
    ]
