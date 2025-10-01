import logging
from flask import request
from zoneinfo import ZoneInfo
from flask_restful import Resource
from datetime import datetime, time, date, timedelta

from services.email_service import Templates
from services.email_service import EmailService
from services.gemini_service import GeminiService
from services.gcal_service import GoogleCalendarService
from database import db, Appointment, AppointmentSchema

logger = logging.getLogger(__name__)

appointment_schema = AppointmentSchema()
appointments_schema = AppointmentSchema(many=True)

DOCTOR_SLOTS = {
    "Dr. Smith": [f"{hour}:00" for hour in range(8, 18)],  # 8AM to 5PM
    "Dr. Lee": [f"{hour}:00" for hour in range(8, 18)],
    "Dr. Patel": [f"{hour}:00" for hour in range(8, 18)],
}

def get_booked_slots(date, doctor=None):
    query = Appointment.query.filter(db.func.date(Appointment.appointment_time) == date)
    if doctor:
        query = query.filter_by(preferred_doctor=doctor)
    response = [a.appointment_time.strftime("%H:%M") for a in query.all()]    
    return response


def find_next_available_slot(start_date=None, doctor=None):
    """Find next available slot from start_date onwards."""
    if not start_date:
        start_date = date.today()
        
    max_days = 30  # limit search to next 30 days
    for i in range(max_days):
        current_date = start_date + timedelta(days=i)
        doctors_to_check = [doctor] if doctor else DOCTOR_SLOTS.keys()
        for doc in doctors_to_check:
            booked_slots = get_booked_slots(current_date, doc)
            for slot in DOCTOR_SLOTS[doc]:
                hour, minute = map(int, slot.split(":"))
                slot_str = slot.zfill(5)
                if slot_str not in booked_slots:
                    hour, minute = map(int, slot.split(":"))
                    return doc, datetime.combine(current_date, time(hour, minute))
    return None, None  # no slots available in next 30 days


class AppointmentListResource(Resource):
    @staticmethod
    def get():
        """Get all appointments"""
        try:
            appointments = Appointment.query.order_by(Appointment.appointment_time.asc()).all()
            return {
                "status": "success",
                "data": appointments_schema.dump(appointments)
            }, 200
        except Exception as e:
            return {"status": "error", "message": f"Unexpected error: {str(e)}"}, 500

    @staticmethod
    def post():
        """Create a new appointment"""
        try:
            json_data = request.get_json(force=True)

            patient_name = json_data.get("patient_name")
            patient_phone = json_data.get("patient_phone")
            patient_email = json_data.get("patient_email")
            date_of_birth_str = json_data.get("date_of_birth")
            symptoms = json_data.get("symptoms")
            appointment_date_str = json_data.get("appointment_date")  # optional
            time_slot = json_data.get("time_slot")  # optional
            preferred_doctor = json_data.get("preferred_doctor")  # optional

            # Validate required fields
            if not all([patient_name, patient_phone, patient_email, date_of_birth_str, symptoms]):
                return {
                    "status": "error",
                    "message": "patient_name, patient_phone, symptoms, and date_of_birth are required"
                }, 400

            # Convert appointment_date if provided
            appointment_date = None
            if appointment_date_str:
                appointment_date = datetime.strptime(appointment_date_str, "%Y-%m-%d").date()

            date_of_birth = datetime.strptime(date_of_birth_str, "%Y-%m-%d").date()

            # Determine final doctor and appointment datetime
            if time_slot and appointment_date:
                # If both date and time provided
                doctor_to_use = preferred_doctor or next(iter(DOCTOR_SLOTS.keys()))
                if time_slot not in DOCTOR_SLOTS[doctor_to_use]:
                    return {
                            "status": "error",
                            "message": "Invalid time slot"
                        }, 400
                if time_slot in get_booked_slots(appointment_date, doctor_to_use):
                    return {
                        "status": "error",
                        "message": "Time slot already booked"
                    }, 400
                hour, minute = map(int, time_slot.split(":"))
                appointment_dt = datetime.combine(appointment_date, time(hour, minute))
                final_doctor = doctor_to_use
            else:
                # Auto-assign next available slot
                final_doctor, appointment_dt = find_next_available_slot(
                    start_date=appointment_date,
                    doctor=preferred_doctor
                )
                if not appointment_dt:
                    return {
                        "status": "error",
                        "message": "No available slots in the next 30 days"
                    }, 400
                

            # 1. Initialize services
            gemini_service = GeminiService()
            gcal_service = GoogleCalendarService()
            email_service = EmailService()

            # 2. Generate summary from symptoms
            summary = gemini_service.summarize_symptoms(
                symptoms=symptoms,
                known_allergies=json_data.get("known_allergies"),
                current_medication=json_data.get("current_medication"),
                medical_history=json_data.get("medical_history"),
                additional_note=json_data.get("additional_note")
            )          

            # 3. Create Google Calendar event
            event_description = (
                f"Symptoms Summary: {summary}\n"
                f"Patient Phone: {patient_phone}\n"
                f"Patient Email: {patient_email}\n"
                f"Doctor: {final_doctor}"
            )

            event_id = gcal_service.create_event(
                summary=patient_name,
                description=event_description,
                start_time=appointment_dt.replace(tzinfo=ZoneInfo("Africa/Addis_Ababa")),
                duration_minutes=60,
                timezone='Africa/Addis_Ababa'
            )
            if not event_id:
                return {"status": "error", "message": "Failed to create calendar event"}, 500

            # 4. Send email to patient using EmailService
            try:
                email_context = {
                    'patient_name': patient_name,
                    'appointment_time': appointment_dt.strftime('%Y-%m-%d %H:%M %Z'),
                    'doctor': final_doctor,
                    'description': summary,
                    'clinic_name': 'CareSync',
                }
                email_sent = email_service.send_email(
                    template=Templates.APPOINTMENT_CONFIRMATION.value,
                    subject=f'Appointment Confirmation: {patient_name}',
                    body_context=email_context,
                    to_email=patient_email,
                )
                if not email_sent:
                    gcal_service.delete_event(event_id)
                    logger.warning(f"Failed to send email to {patient_email}, but event created.")

            except Exception as e:
                logger.warning(f"Failed to send email to {patient_email}: {e}, deleting event {event_id}")
                gcal_service.delete_event(event_id)
                return {"status": "error", "message": f"Failed to send email: {str(e)}"}, 500

            # 5. Create and save the new appointment to the database
            try:
                new_appointment = Appointment(
                    patient_name=patient_name,
                    patient_phone=patient_phone,
                    patient_email=patient_email,
                    date_of_birth=date_of_birth,
                    symptoms=symptoms,
                    summary=summary,
                    appointment_time=appointment_dt,
                    preferred_doctor=final_doctor,
                    google_calendar_event_id=event_id,

                    gender=json_data.get("gender"),
                    known_allergies=json_data.get("known_allergies"),
                    current_medication=json_data.get("current_medication"),
                    medical_history=json_data.get("medical_history"),
                    additional_note=json_data.get("additional_note")
                )
                db.session.add(new_appointment)
                db.session.commit()

            except Exception as e:
                logger.warning(f"Failed to save appointment to database: {e}, deleting event {event_id}")
                gcal_service.delete_event(event_id)
                db.session.rollback()
                return {"status": "error", "message": f"Failed to save appointment to database: {str(e)}"}, 500

            return {
                "status": "success",
                "message": "Appointment created successfully",
                "data": appointment_schema.dump(new_appointment)
            }, 201            
            
        except Exception as e:
            db.session.rollback()
            if 'event_id' in locals():
                logger.warning(f"Unexpected error occurred, deleting event {event_id}")
                gcal_service.delete_event(event_id)
            return {"status": "error", "message": f"Unexpected error: {str(e)}"}, 500