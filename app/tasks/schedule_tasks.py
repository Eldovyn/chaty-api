import datetime
from ..models import AccountActiveModel, ResetPasswordModel, OtpEmailModel
from celery.schedules import crontab


def register_tasks(celery_app):
    @celery_app.task(name="update_data_every_10_minutes")
    def update_data_every_10_minutes():
        now = datetime.datetime.now(datetime.timezone.utc)

        for model, name in [
            (AccountActiveModel, "account active"),
            (ResetPasswordModel, "reset password"),
            (OtpEmailModel, "otp email"),
        ]:
            for data in model.objects.all():
                data_expired_at = getattr(data, "expired_at", None)

                if data_expired_at and data_expired_at.tzinfo is None:
                    data_expired_at = data_expired_at.replace(
                        tzinfo=datetime.timezone.utc
                    )

                is_expired = data_expired_at and data_expired_at <= now
                is_user_active = getattr(data.user, "is_active", False)

                if is_expired or is_user_active:
                    data.delete()
                    print(f"success delete token {name} {data.user.email}")

        return "clear data"

    celery_app.conf.beat_schedule = {
        "run-every-5-minutes": {
            "task": "update_data_every_10_minutes",
            "schedule": crontab(minute="*/5"),
        },
    }
