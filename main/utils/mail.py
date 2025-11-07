from django.core.mail import send_mail

def send_email(subject, message, recipient_list, from_email='stemappza@gmail.com', fail_silently=False):
    """
    Utility function to send emails.
    :param subject: Subject of the email
    :param message: Body of the email
    :param recipient_list: List of recipient email addresses
    :param from_email: Sender email address (default: stemappza@gmail.com)
    :param fail_silently: Whether to suppress errors (default: False)
    """
    send_mail(
        subject,
        message,
        from_email,
        recipient_list,
        fail_silently=fail_silently,
    )