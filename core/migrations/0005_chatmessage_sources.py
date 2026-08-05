# Generated for document-chat source citations.
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0004_userprofile")]

    operations = [
        migrations.AddField(
            model_name="chatmessage",
            name="sources",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
