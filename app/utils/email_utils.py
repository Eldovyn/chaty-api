from flask_mail import Message


def send_email(subject, recipients, body):
    from ..extensions import mail

    msg = Message(subject, recipients=recipients)
    msg.html = body
    mail.send(msg)
