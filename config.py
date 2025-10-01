import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv(
            "DATABASE_URL",
            f"sqlite:///{os.path.join(basedir, 'patients.db')}"
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

    GOOGLE_CREDENTIALS_PATH = os.getenv('GOOGLE_CREDENTIALS_PATH')
    GOOGLE_CALENDAR_ID = os.getenv('GOOGLE_CALENDAR_ID')