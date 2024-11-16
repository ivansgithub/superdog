# auth_utils.py
import requests
import base64
from jwt import decode, ExpiredSignatureError, InvalidTokenError
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
from cryptography.hazmat.backends import default_backend
from flask import request, jsonify, current_app
from functools import wraps
import jwt 

def get_public_key(kid):
    jwks_url = f"https://cognito-idp.{current_app.config['AWS_COGNITO_REGION']}.amazonaws.com/{current_app.config['AWS_COGNITO_USER_POOL_ID']}/.well-known/jwks.json"
    response = requests.get(jwks_url)
    jwks = response.json()
    
    for key in jwks['keys']:
        if key['kid'] == kid:
            n = int.from_bytes(base64.urlsafe_b64decode(key['n'] + '=='), byteorder='big')
            e = int.from_bytes(base64.urlsafe_b64decode(key['e'] + '=='), byteorder='big')
            public_numbers = RSAPublicNumbers(e, n)
            return public_numbers.public_key(default_backend())
    return None


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token de autenticación es requerido'}), 401
        
        token = token.split("Bearer ")[1] if "Bearer " in token else token
        try:
            # Obtener los encabezados sin verificar el token
            headers = jwt.get_unverified_header(token)
            kid = headers['kid']
            
            # Obtener la clave pública para este token
            public_key = get_public_key(kid)
            if not public_key:
                return jsonify({'error': 'Clave pública no encontrada para el token proporcionado.'}), 401
            
            # Decodificar el token usando la clave pública
            payload = jwt.decode(
                token,
                key=public_key,
                algorithms=["RS256"],
                options={"require": ["exp", "iat"]}
            )
            request.user = payload
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'El token ha expirado'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token inválido'}), 401
        return f(*args, **kwargs)
    return decorated


