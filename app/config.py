import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key'
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, '../instance/database.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    AWS_COGNITO_USER_POOL_ID = 'us-east-1_SynwYWMzT'
    AWS_COGNITO_REGION = 'us-east-1' 
    AWS_COGNITO_CLIENT_ID = '49cmo5m9np2slmi2dbb2erl3iu'
    AWS_COGNITO_PUBLIC_KEY = '-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkq...-----END PUBLIC KEY-----\n'
