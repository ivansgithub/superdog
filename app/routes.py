from flask import request, jsonify, Blueprint, render_template, flash, url_for, redirect, current_app
from .extensions import db
from .models import User, Space, Bid, Auction
from . import socketio
from datetime import datetime, timedelta
from flask_login import login_user, logout_user, login_required, current_user
import boto3
from functools import wraps
from .auth import get_public_key, token_required
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
import jwt

main = Blueprint('main', __name__)
auth_bp = Blueprint('auth', __name__)

# ---- AUTENTICACIÓN ----

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    if request.method == 'POST':
        try:
            # Verifica y parsea los datos JSON correctamente
            data = request.get_json(force=True)  # Asegura que siempre se procesa como JSON
            if not data or 'username' not in data or 'password' not in data:
                return jsonify({'error': 'Faltan campos requeridos: username y password'}), 400
           
            username = data['username']
            password = data['password']

            cognito_client = boto3.client('cognito-idp', region_name=current_app.config['AWS_COGNITO_REGION'])

            response = cognito_client.initiate_auth(
                ClientId=current_app.config['AWS_COGNITO_CLIENT_ID'],
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters={
                    'USERNAME': username,
                    'PASSWORD': password,
                }
            )

            token = response['AuthenticationResult']['AccessToken']
            id_token = response['AuthenticationResult']['IdToken']

            decoded_token = jwt.decode(id_token, options={"verify_signature": False})
            cognito_id = decoded_token['sub']
            username = decoded_token.get('cognito:username', username)

            # Crear o actualizar el usuario en la base de datos
            user = User.query.get(cognito_id)
            if not user:
                user = User(id=cognito_id, username=username)
                db.session.add(user)
            else:
                user.username = username
            db.session.commit()

            return jsonify({'message': 'Inicio de sesión exitoso', 'token': token}), 200

        except cognito_client.exceptions.NotAuthorizedException:
            return jsonify({'error': 'Usuario o contraseña incorrectos'}), 401
        except cognito_client.exceptions.UserNotFoundException:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        except Exception as e:
            return jsonify({'error': f'Error de autenticación: {str(e)}'}), 400




@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')

        cognito_client = boto3.client('cognito-idp', region_name=current_app.config['AWS_COGNITO_REGION'])
        
        try:
            cognito_client.sign_up(
                ClientId=current_app.config['AWS_COGNITO_CLIENT_ID'],
                Username=username,
                Password=password,
                UserAttributes=[{'Name': 'email', 'Value': email}]
            )
            return jsonify({'message': 'Registro exitoso. Revisa tu correo para confirmar la cuenta.'}), 201
        except cognito_client.exceptions.UsernameExistsException:
            return jsonify({'error': 'El nombre de usuario ya está registrado.'}), 409
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return render_template('register.html')  # Renderizar formulario de registro en solicitudes GET



@auth_bp.route('/confirm', methods=['POST'])
def confirm_registration():
    data = request.json
    username = data.get('username')
    code = data.get('code')

    cognito_client = boto3.client('cognito-idp', region_name=current_app.config['AWS_COGNITO_REGION'])

    try:
        cognito_client.confirm_sign_up(
            ClientId=current_app.config['AWS_COGNITO_CLIENT_ID'],
            Username=username,
            ConfirmationCode=code
        )
        return jsonify({'message': 'Cuenta confirmada exitosamente. Ahora puedes iniciar sesión.'}), 200
    except cognito_client.exceptions.CodeMismatchException:
        return jsonify({'error': 'Código de verificación incorrecto.'}), 400
    except cognito_client.exceptions.ExpiredCodeException:
        return jsonify({'error': 'El código de verificación ha expirado.'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/profile', methods=['GET'])
@token_required
def profile():
    user_data = request.user
    # Agregar esta línea
    return jsonify({'user': {'id': user_data['sub'], 'username': user_data['username']}}), 200



# ---- SUBASTAS ----

@socketio.on('bid')
def handle_bid(data):
    token = data.get('token')  # El cliente envía el token en cada puja
    space_id = data.get('space_id')
    amount = data.get('amount')
    
    

    try:
        # Decodificar el token y extraer el sub
        decoded_token = jwt.decode(token, options={"verify_signature": False})  # Ajusta según tus necesidades
        user_id = decoded_token['sub']

        # Buscar al usuario en la base de datos
        user = User.query.get(user_id)
        if not user:
            socketio.emit('bid_error', {'error': 'Usuario no encontrado en la base de datos.'})
            return

        # Buscar el espacio y la subasta activa
        space = Space.query.get(space_id)
        if not space:
            socketio.emit('bid_error', {'error': 'Espacio no encontrado.'})
            return

        if not space.auctions:
            socketio.emit('bid_error', {'error': 'No hay subasta activa para este espacio.'})
            return

        auction_id = space.auctions[0].id
        highest_bid = db.session.query(db.func.max(Bid.amount)).filter(Bid.auction_id == auction_id).scalar() or 0.0

        # Verificar la nueva puja
        if amount > highest_bid:
            # Crear una nueva puja
            new_bid = Bid(amount=amount, user_id=user_id, auction_id=auction_id)
            space.current_bid = amount
            db.session.add(new_bid)
            db.session.commit()

            # Emitir la actualización de la puja
            socketio.emit('bid_update', {
                'space_id': space_id,
                'current_bid': amount,
                'user_name': user.username  # Usar el nombre del usuario
            })
        else:
            socketio.emit('bid_error', {'error': 'La puja debe ser mayor a la actual.'})

    except jwt.ExpiredSignatureError:
        socketio.emit('bid_error', {'error': 'Token expirado. Inicia sesión nuevamente.'})
    except jwt.InvalidTokenError:
        socketio.emit('bid_error', {'error': 'Token inválido.'})


@main.route('/get_spaces_info')
def get_spaces_info():
    spaces_data = []
    spaces = Space.query.all()

    columns = 4
    for index, space in enumerate(spaces):
        row_label = chr(65 + (index // columns))
        col_label = (index % columns) + 1
        position = f"{row_label}{col_label}"

        auction = Auction.query.filter_by(space_id=space.id).order_by(Auction.start_time.desc()).first()
        highest_bid = db.session.query(db.func.max(Bid.amount)).filter(Bid.auction_id == auction.id).scalar() if auction else 0.0
        highest_bidder = db.session.query(User.username).join(Bid).filter(Bid.auction_id == auction.id, Bid.amount == highest_bid).scalar() if auction and highest_bid else 'Ninguno'

        spaces_data.append({
            'space_id': space.id,
            'position': position,
            'size': space.size,
            'status': space.status,
            'current_bid': highest_bid or 0.0,
            'highest_bidder': highest_bidder,
            'start_time': auction.start_time if auction else None,
            'end_time': auction.end_time if auction else None,
        })

    return jsonify(spaces_data), 200


@main.route('/auction')
def auction():
    return render_template('auction.html')


@main.route('/create_test_spaces')
def create_test_spaces():
    for i in range(16):
        space = Space(position_x=i % 4, position_y=i // 4, size="small", status="available")
        db.session.add(space)
        db.session.commit()

        auction = Auction(
            space_id=space.id,
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow() + timedelta(minutes=10)
        )
        db.session.add(auction)
        db.session.commit()
    return jsonify({'message': 'Espacios y subastas creados.'}), 201


# ---- SESIONES ----

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada.')
    return redirect(url_for('auth.login'))
