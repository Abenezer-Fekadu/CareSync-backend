import os
import logging
from twilio.rest import Client

# Create a dedicated logger for SmsService
logger = logging.getLogger('services.SmsService')

class SmsTemplateManager:    
    TEMPLATES = {
        "APPOINTMENT_CONFIRMATION_SMS": {
            "template": "Hi {patient_name}, your appointment with {doctor} at CareSync is confirmed for {appointment_time}. Contact us if needed.",
            "required_params": ["patient_name", "doctor", "appointment_time"],
        },
        "APPOINTMENT_REMINDER_SMS": {
            "template": "Reminder: {patient_name}, you have an appointment with {doctor} at CareSync on {appointment_time}. Please arrive early.",
            "required_params": ["patient_name", "doctor", "appointment_time"],
        },
    }

    def load_template(self, template_name: str, data: dict) -> str: 
        template_data = self.TEMPLATES.get(template_name)
        if not template_data:
            raise ValueError(f"Template '{template_name}' is not defined.")

        template = template_data["template"]
        required_params = template_data["required_params"]
        for param in required_params:
            if param not in data:
                raise ValueError(f"Missing required parameter '{param}' for template '{template_name}'")

        return template.format(**data)


class SmsService:
    def __init__(self):
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        
        if not account_sid or not auth_token:
            raise ValueError('Twilio credentials are not set correctly')
        self.client = Client(account_sid, auth_token)
        self.template_manager = SmsTemplateManager()

    def send_sms(self, data):
        try:
            from_phone = os.getenv('TWILIO_FROM_PHONE')
            to_phone = data.get('phone_number')

            # Message
            template_name = data.get("template")
            message_body = self.template_manager.load_template(template_name, data)

            if not from_phone:
                raise ValueError('Invalid sender phone number')
            if not to_phone:
                raise ValueError('Invalid recipient phone number')

            message = self.client.messages.create(
                body=message_body,
                from_=from_phone,
                to=to_phone
            )

            logger.info(f"SmsService [send_sms]: SMS sent to {to_phone}, SID: {message.sid}")
            return message.sid
        except Exception as e:
            logger.error(f"SmsService [send_sms]: Error sending SMS: {str(e)}")
            return None