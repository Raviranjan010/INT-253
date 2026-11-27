from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('certificates', '0002_certificate_digital_signature')]
    operations = [
        migrations.AddField(
            model_name='certificate', name='signature_version',
            field=models.PositiveSmallIntegerField(default=1, editable=False),
        ),
        migrations.AlterField(
            model_name='certificate', name='signature_version',
            field=models.PositiveSmallIntegerField(default=2, editable=False),
        ),
        migrations.AlterField(
            model_name='certificate', name='course',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='issued_certificates', to='courses.course'),
        ),
    ]
