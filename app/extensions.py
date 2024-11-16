# app/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
import boto3
from flask import current_app

def get_cognito_client():
    # Crea y devuelve el cliente de Cognito, tomando los valores de configuración de la aplicación
    return boto3.client('cognito-idp', region_name=current_app.config['AWS_COGNITO_REGION'])


db = SQLAlchemy()
socketio = SocketIO(cors_allowed_origins="*")
