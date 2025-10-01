import pytz
import logging
from flask_restful import Resource
from datetime import datetime, timedelta

from database import db, Appointment, AppointmentSchema
from services.email_service import EmailService, Templates

# Configure logging
logger = logging.getLogger(__name__)

appointments_schema = AppointmentSchema(many=True)

class SendRemindersResource(Resource):
    @staticmethod
    def post():
        """Find appointments needing reminders and send emails"""
        try:
            timezone = pytz.timezone('Africa/Addis_Ababa')
            now = datetime.now(timezone)
            reminder_window_start = now
            reminder_window_end = now + timedelta(hours=24)

            appointments_to_remind = Appointment.query.filter(
                Appointment.appointment_time >= reminder_window_start,
                Appointment.appointment_time < reminder_window_end,
                Appointment.reminder_sent == False
            ).order_by(Appointment.id.desc()).all()

            if not appointments_to_remind:
                logger.info("No appointments found needing reminders.")
                return {"status": "success", "message": "No appointments to remind."}, 200

            logger.info(f"Found {len(appointments_to_remind)} appointments to remind.")
            email_service = EmailService()
            reminders_sent = 0

            for appt in appointments_to_remind:
                email_success = False
                email_time_str = appt.appointment_time.strftime('%Y-%m-%d %H:%M %Z')
                email_context = {
                    'patient_name': appt.patient_name,
                    'appointment_time': email_time_str,
                    'doctor': appt.preferred_doctor,
                    'description': appt.summary,
                    'clinic_name': 'CareSync',
                }

                try:
                    email_sent = email_service.send_email(
                        template=Templates.APPOINTMENT_REMINDER.value,
                        subject=f'Appointment Reminder: {appt.patient_name}',
                        body_context=email_context,
                        to_email=appt.patient_email
                    )
                    if email_sent:
                        email_success = True
                        logger.info(f"Email sent for appointment {appt.id} to {appt.patient_email}")
                    else:
                        logger.warning(f"Failed to send email for appointment {appt.id}")
                except Exception as e:
                    logger.warning(f"Exception sending email for appointment {appt.id}: {str(e)}")

                if email_success:
                    appt.reminder_sent = True
                    db.session.commit()
                    reminders_sent += 1

            logger.info(f"Completed reminders. Sent {reminders_sent} emails.")
            return {
                "status": "success",
                "message": f"Sent {reminders_sent} reminders."
            }, 200

        except Exception as e:
            logger.error(f"Error in sending reminders: {str(e)}")
            return {"status": "error", "message": str(e)}, 500
