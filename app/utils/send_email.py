class SendEmail:
    @staticmethod
    def send_email(subject, recipients, body):
        from ..tasks import send_email_task

        send_email_task.apply_async(
            args=[
                subject,
                recipients,
                body,
            ],
        )
