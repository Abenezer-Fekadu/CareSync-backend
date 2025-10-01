import pytz
from datetime import datetime
from marshmallow import fields

from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy

from sqlalchemy import Index, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import Integer, String, Text, DateTime, Boolean


db = SQLAlchemy()
ma= Marshmallow()

class Appointment(db.Model):
    """
    Appointment table to store patient appointments and reminders.
    """
    __tablename__ = "appointments"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_appointment"),
        Index("idx_appointment_id", "id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_name: Mapped[str] = mapped_column(String(100), nullable=False)
    patient_email: Mapped[str] = mapped_column(String(100), nullable=False)  # New
    patient_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    date_of_birth: Mapped[datetime] = mapped_column(DateTime, nullable=False)  # New
    gender: Mapped[str] = mapped_column(String(20), nullable=True)
    known_allergies: Mapped[str] = mapped_column(Text, nullable=True)
    current_medication: Mapped[str] = mapped_column(Text, nullable=True)
    medical_history: Mapped[str] = mapped_column(Text, nullable=True)
    preferred_doctor: Mapped[str] = mapped_column(String(100), nullable=True)
    additional_note: Mapped[str] = mapped_column(Text, nullable=True)

    symptoms: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=True)
    appointment_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    google_calendar_event_id: Mapped[str] = mapped_column(String(100), nullable=True)
    reminder_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(pytz.utc), nullable=False)


class AppointmentSchema(ma.Schema):
    id = fields.Int(dump_only=True)
    patient_name = fields.Str(required=True)
    patient_email = fields.Email(required=True)
    patient_phone = fields.Str(required=True)
    date_of_birth = fields.Date(required=True)
    gender = fields.Str(required=False, allow_none=True)
    known_allergies = fields.Str(required=False, allow_none=True)
    current_medication = fields.Str(required=False, allow_none=True)
    medical_history = fields.Str(required=False, allow_none=True)
    preferred_doctor = fields.Str(required=False, allow_none=True)
    additional_note = fields.Str(required=False, allow_none=True)

    symptoms = fields.Str(required=True)
    summary = fields.Str(required=False, allow_none=True)
    appointment_time = fields.DateTime(required=False)
    google_calendar_event_id = fields.Str(dump_only=True, allow_none=True)
    reminder_sent = fields.Bool(dump_only=True)
    created_at = fields.DateTime(dump_only=True)

    # <-- Add these optional fields for frontend requests
    appointment_date = fields.Date(required=False, allow_none=True)
    time_slot = fields.Str(required=False, allow_none=True)