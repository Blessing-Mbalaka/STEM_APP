from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("main", "0025_tutorapplicationdocument_doc_type")]

    operations = [
        migrations.AddField(
            model_name="customuser", name="languages",
            field=models.JSONField(blank=True, default=list, null=True),
        ),
        migrations.AddField(
            model_name="classsession", name="price",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name="classsession", name="language",
            field=models.CharField(blank=True, default="", max_length=50),
        ),
        migrations.AddField(
            model_name="reservation", name="payment_status",
            field=models.CharField(choices=[("not_required", "Not required"), ("pending", "Awaiting payment verification"), ("approved", "Payment approved"), ("rejected", "Payment rejected")], default="not_required", max_length=20),
        ),
        migrations.AddField(
            model_name="message", name="attachment",
            field=models.FileField(blank=True, null=True, upload_to="message_attachments/%Y/%m/"),
        ),
    ]
