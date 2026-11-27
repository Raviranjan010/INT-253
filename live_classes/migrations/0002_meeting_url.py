from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('live_classes', '0001_initial')]
    operations = [
        migrations.AddField(
            model_name='livesession', name='meeting_url', field=models.URLField(blank=True),
        ),
    ]
