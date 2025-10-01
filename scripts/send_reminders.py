import sys
import os
import pytz
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Make app modules available
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from database import db, Appointment
from services.email_service import EmailService, Templates

def find_and_send_reminders():
    """Finds appointments needing reminders and sends them via email."""
    app = create_app()
    with app.app_context():
        
        logger.info("Starting reminder check...")
        
        timezone = pytz.timezone('Africa/Addis_Ababa')
        now = datetime.now(timezone)
        reminder_window_start = now
        reminder_window_end = now + timedelta(hours=24)

        appointments_to_remind = Appointment.query.filter(
            Appointment.appointment_time >= reminder_window_start,
            Appointment.appointment_time < reminder_window_end,
            Appointment.reminder_sent == False
        ).all()

        if not appointments_to_remind:
            logger.info("No appointments found needing reminders.")
            return

        logger.info(f"Found {len(appointments_to_remind)} appointments to remind.")
        email_service = EmailService()
        reminders_sent = 0
        
        for appt in appointments_to_remind:
            # Format the time for email

            email_time_str = appt.appointment_time.strftime('%Y-%m-%d %H:%M %Z')
            email_context = {
                'patient_name': appt.patient_name,
                'appointment_time': email_time_str,
                'doctor': appt.preferred_doctor,
                'description': appt.summary,
                'clinic_name': 'CareSync',
            }

            # Send Email
            try:
                email_sent = email_service.send_email(
                    template=Templates.APPOINTMENT_REMINDER,
                    subject=f'Appointment Reminder: {appt.patient_name}',
                    body_context=email_context,
                    to_email=appt.patient_email
                )
                if email_sent:
                    email_success = True
                    logger.info(f"Successfully sent email reminder for appointment {appt.id} to {appt.patient_email}")
                    break
                else:
                    logger.warning(f"Failed to send email reminder for appointment {appt.id} to {appt.patient_email}, status code: {email_service.last_status_code}")
            except Exception as e:
                logger.warning(f"Failed to send email reminder for appointment {appt.id} to {appt.patient_email}: {str(e)}")

            # Update reminder_sent only if email sent
            if email_success:
                appt.reminder_sent = True
                db.session.commit()
                reminders_sent += 1
                logger.info(f"Successfully sent reminders for appointment {appt.id} and updated database")
            else:
                logger.warning(f"Reminder for appointment {appt.id}, Email: {email_success})")

        logger.info(f"Completed reminder check. Sent reminders for {reminders_sent} appointments.")

if __name__ == '__main__':
    find_and_send_reminders()