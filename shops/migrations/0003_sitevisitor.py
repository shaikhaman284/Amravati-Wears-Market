# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shops', '0002_alter_shop_shop_image'),
    ]

    operations = [
        migrations.CreateModel(
            name='SiteVisitor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip_address', models.GenericIPAddressField()),
                ('user_agent', models.TextField(blank=True, null=True)),
                ('visited_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'site_visitors',
                'ordering': ['-visited_at'],
            },
        ),
        migrations.AddIndex(
            model_name='sitevisitor',
            index=models.Index(fields=['ip_address', 'visited_at'], name='site_visito_ip_addr_idx'),
        ),
    ]
