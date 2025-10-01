import os
from pathlib import Path
from flask_cors import CORS
from flask_restful import Api
from dotenv import load_dotenv
from flask_migrate import Migrate
from flask import Flask, Blueprint

from database import db
from api.appointment import AppointmentListResource
from api.available_slots import AvailableSlotsResource
from api.appointment_reminder import SendRemindersResource

# Load environment variables from .env
env_file_name = ".env"
env_path = Path.cwd().joinpath(f"{env_file_name}")
load_dotenv(dotenv_path=env_path)

# Import config after loading environment variables to avoid errors
from config import Config


# Create blueprint for API
api_bp = Blueprint("api", __name__)
api = Api(api_bp)
api.add_resource(AppointmentListResource, "/appointments")
api.add_resource(AvailableSlotsResource, '/available-slots')
api.add_resource(SendRemindersResource, "/send-reminders")

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    CORS(app)

    with app.app_context():
        db.init_app(app)
        Migrate(app, db)

    # Register blueprint
    app.register_blueprint(api_bp, url_prefix="/api")
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)