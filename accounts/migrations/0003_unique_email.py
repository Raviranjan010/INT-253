from django.db import migrations, models
from django.db.models.functions import Lower


def check_duplicates(apps, schema_editor):
    users = apps.get_model('accounts', 'CustomUser').objects.using(schema_editor.connection.alias)
    duplicates = list(
        users.exclude(email='').annotate(normalized=Lower('email')).values('normalized')
        .annotate(total=models.Count('pk')).filter(total__gt=1).order_by('normalized')[:20]
    )
    if duplicates:
        groups = [list(users.filter(email__iexact=row['normalized']).values_list('pk', flat=True)) for row in duplicates]
        raise RuntimeError(f'Resolve duplicate email addresses for these account ID groups before retrying: {groups}')


class Migration(migrations.Migration):
    dependencies = [('accounts', '0002_customuser_is_instructor_approved_xpledger')]
    operations = [
        migrations.RunPython(check_duplicates, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='customuser',
            constraint=models.UniqueConstraint(Lower('email'), condition=~models.Q(email=''), name='accounts_email_ci_unique'),
        ),
    ]
