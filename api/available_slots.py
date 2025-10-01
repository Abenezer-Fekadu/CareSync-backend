from flask import request
from flask_restful import Resource
from datetime import datetime, time, date, timedelta

from api.appointment import DOCTOR_SLOTS, get_booked_slots

class AvailableSlotsResource(Resource):
    @staticmethod
    def post():
        """Get available time slots for a specific doctor on a specific date"""
        try:
            json_data = request.get_json(force=True)
            doctor = json_data.get("doctor")
            date_str = json_data.get("date")

            # Validate required fields
            if not doctor or not date_str:
                return {
                    "status": "error",
                    "message": "doctor and date are required"
                }, 400

            # Validate doctor
            if doctor not in DOCTOR_SLOTS:
                return {
                    "status": "error",
                    "message": f"Invalid doctor. Available doctors: {list(DOCTOR_SLOTS.keys())}"
                }, 400

            # Parse date
            try:
                appointment_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return {
                    "status": "error",
                    "message": "Invalid date format. Use YYYY-MM-DD"
                }, 400

            # Get booked slots for the date and doctor
            booked_slots = get_booked_slots(appointment_date, doctor)

            # Calculate available slots
            available_slots = [slot for slot in DOCTOR_SLOTS[doctor] if slot not in booked_slots]

            return {
                "status": "success",
                "message": f"Available slots for {doctor} on {date_str}",
                "data": {
                    "doctor": doctor,
                    "date": date_str,
                    "available_slots": available_slots
                }
            }, 200

        except Exception as e:
            return {"status": "error", "message": f"Unexpected error: {str(e)}"}, 500