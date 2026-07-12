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


def send_class_payment_received_email(reservation):
    """Notify a learner only after a tutor has verified funds for a paid class."""
    user = reservation.user
    session = reservation.session
    if not user.email:
        return False
    amount = f"R{session.price:.2f}"
    message = f"""Hello {user.display_name or user.username},

Payment received. Your payment of {amount} for “{session.title}” has been verified by your tutor.

Your class access is now released.
Class link: {session.location or 'The tutor will add the class link shortly.'}
Class time: {session.starts_at.strftime('%d %B %Y at %H:%M')}

You can also find this confirmation in your STEM LMS messages.

Regards,
STEM LMS System
"""
    send_email(
        subject=f"Payment received — {session.title}",
        message=message,
        recipient_list=[user.email],
        fail_silently=True,
    )
    return True


def send_learner_welcome_email(user):
    """
    Send a welcome email to a new learner after registration.
    :param user: CustomUser instance
    """
    if not user.email:
        return False
    
    subject = 'Welcome to STEM LMS!'
    message = f"""Hello {user.display_name or user.username},

Thank you for registering with STEM LMS! Your account has been successfully created.

You can now log in and start exploring our platform:
- Browse courses
- Connect with tutors
- Participate in games and quizzes
- Join our learning community

If you have any questions, feel free to reach out to our support team.

Happy learning!

Best regards,
STEM LMS Team
"""
    
    send_email(
        subject=subject,
        message=message,
        recipient_list=[user.email],
        fail_silently=True,
    )
    return True


def send_tutor_application_received_email(user):
    """
    Send a confirmation email to a tutor after application submission.
    :param user: CustomUser instance
    """
    if not user.email:
        return False
    
    subject = 'Tutor Application Received - STEM LMS'
    message = f"""Hello {user.display_name or user.username},

Thank you for applying to become a tutor at STEM LMS!

We have received your application and have started the review process. Our admin team will carefully review your qualifications and documents.

You will receive an email notification once your application has been reviewed. This typically takes 1-3 business days.

In the meantime, if you have any questions, please don't hesitate to contact us.

Best regards,
STEM LMS Team
"""
    
    send_email(
        subject=subject,
        message=message,
        recipient_list=[user.email],
        fail_silently=True,
    )
    return True


def send_tutor_approval_email(user):
    """
    Send an approval email to a tutor whose application was approved.
    :param user: CustomUser instance
    """
    if not user.email:
        return False
    
    subject = 'Tutor Application Approved - STEM LMS'
    message = f"""Hello {user.display_name or user.username},

Great news! Your tutor application has been approved.

Your account is now active and you can start using the tutor features:
- Create classes and sessions
- Manage students
- Access the tutor dashboard
- Track your teaching sessions

Please log in to your account to get started: https://www.stemlms.com/

Congratulations and welcome to the STEM LMS tutor community!

Best regards,
STEM LMS Team
"""
    
    send_email(
        subject=subject,
        message=message,
        recipient_list=[user.email],
        fail_silently=True,
    )
    return True


def send_tutor_rejection_email(user, notes=None):
    """
    Send a rejection email to a tutor whose application was rejected.
    :param user: CustomUser instance
    :param notes: Optional notes from the admin about the rejection
    """
    if not user.email:
        return False
    
    subject = 'Tutor Application Status Update - STEM LMS'
    feedback = ""
    if notes:
        feedback = f"\nFeedback from our admin team:\n{notes}\n"
    
    message = f"""Hello {user.display_name or user.username},

Thank you for your interest in becoming a tutor at STEM LMS.

After careful review of your application and documents, we have decided not to move forward at this time. This decision is based on our assessment of the qualifications and requirements for our tutor program.{feedback}
We encourage you to address any feedback and feel free to reapply in the future. If you have questions about this decision, please contact our support team.

Best regards,
STEM LMS Team
"""
    
    send_email(
        subject=subject,
        message=message,
        recipient_list=[user.email],
        fail_silently=True,
    )
    return True
