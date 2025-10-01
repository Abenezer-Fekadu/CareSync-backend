import os
import logging
from enum import Enum
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, From, To

logger = logging.getLogger(__name__)

class Templates(Enum):
    APPOINTMENT_REMINDER = 'appointment_reminder.html'
    APPOINTMENT_CONFIRMATION = 'appointment_confirmation.html'

    APPOINTMENT_REMINDER_SMS = 'APPOINTMENT_REMINDER_SMS'
    APPOINTMENT_CONFIRMATION_SMS = 'APPOINTMENT_CONFIRMATION_SMS'
    
class EmailService:
    def __init__(self):
        """Initializes the SendGrid client."""
        self.api_key = os.getenv('SENDGRID_API_KEY')
        if not self.api_key:
            raise ValueError("SENDGRID_API_KEY environment variable not set.")
        
        self.templates_folder = os.getenv('EMAIL_TEMPLATES_FOLDER')
        if not self.templates_folder:
            raise ValueError("EMAIL_TEMPLATES_FOLDER environment variable not set.")
        
        if not os.path.isdir(self.templates_folder):
            raise FileNotFoundError(f"Email templates folder not found at: {self.templates_folder}")

        self.sg = SendGridAPIClient(self.api_key)
        self.sender_name = 'CareSync'
        self.from_email = os.getenv('EMAIL_FROM')
        if not self.from_email:
            raise ValueError("EMAIL_FROM environment variable not set.")
        
        logger.info("EmailService initialized successfully.")

    def load_template(self, template, body):
        folder = os.getenv('EMAIL_TEMPLATES_FOLDER')
        if not folder:
            raise ValueError('Invalid email templates folder')
        with open(f"{folder}/{template}") as f:
            file = f.read()
            for key, value in body.items():
                file = file.replace(f"{{{key}}}", value)
            return file

    def send_email(self, to_email: str, subject: str, template: str, body_context: dict):
        if not to_email or not subject or not template:
            raise ValueError("to_email, subject, and template are required.")
            
        try:
            html_content = self.load_template(template, body_context)
            message = Mail(
                from_email=From(self.from_email, self.sender_name),
                to_emails=To(to_email),
                subject=subject,
                html_content=html_content
            )

            response = self.sg.send(message)
            logger.info(f"Email sent to {to_email} with subject '{subject}'. Status Code: {response.status_code}")
            return response

        except PermissionError as e:
            print(e)
            logger.error(f"Could not send email due to a template security issue: {e}")
            raise 
        except Exception as e:
            print(e)
            logger.error(f"Failed to send email to {to_email}: {e}")
            raise
