from flask import request, jsonify, Blueprint, render_template
from .extensions import db
from .models import User, Space, Bid
from . import socketio
from datetime import datetime, timedelta

main = Blueprint('main', __name__)

@socketio.on('bid')
def handle_bid(data):
    user_id = data.get('user_id')
    space_id = data.get('space_id')
    amount = data.get('amount')
    
    print(f"Recibida puja para espacio {space_id} con monto {amount} por usuario {user_id}")

    user = User.query.get(user_id)
    space = Space.query.get(space_id)

    if not user or not space:
        socketio.emit('bid_error', {'error': 'Usuario o espacio no encontrado.'}, to='/', include_self=True)
        return

    # Verificar que haya una subasta activa para el espacio
    if not space.auctions:
        socketio.emit('bid_error', {'error': 'No hay subasta activa para este espacio.'})
        return

    # Obtener el auction_id específico del espacio actual
    auction_id = space.auctions[0].id
    print(f"Auction ID para espacio {space_id}: {auction_id}")

    # Obtener el highest_bid específico para esta subasta
    highest_bid = db.session.query(db.func.max(Bid.amount)).filter(Bid.auction_id == auction_id).scalar() or 0.0
    print(f"Calculando highest_bid para espacio {space_id} en subasta {auction_id}: Puja más alta actual es {highest_bid}")

    # Verificar que la nueva puja sea mayor al highest_bid actual
    if amount > highest_bid:
        # Crear nueva puja y actualizar el estado del espacio
        new_bid = Bid(amount=amount, user_id=user_id, auction_id=auction_id)
        space.current_bid = amount  # Actualizar space.current_bid al nuevo valor de puja
        space.status = "in auction"  # Cambiar el estado del espacio si está en subasta
        db.session.add(new_bid)
        db.session.commit()
        
        # Emitir evento bid_update con los detalles actualizados
        print(f"Emitiendo bid_update para espacio {space_id} con puja {amount} por usuario {user.name}")
        socketio.emit('bid_update', {
            'space_id': space_id,
            'current_bid': amount,
            'user_name': user.name
        })
    else:
        # Emitir un mensaje de error si la puja no es válida
        socketio.emit('bid_error', {'error': 'La puja debe ser mayor que la actual.'})


@socketio.on('connect')
def handle_connect():
    print("Client connected")

@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected")

@main.route('/create_test_user')
def create_test_user():
    # Crear un usuario de prueba
    test_user = User(name="Test User", email="testuser@example.com", password="password123")
    db.session.add(test_user)
    db.session.commit()
    return jsonify({"message": "Usuario de prueba creado"})

@main.route('/get_users')
def get_users():
    users = User.query.all()  # Consulta todos los usuarios
    user_list = [{"id": user.id, "name": user.name, "email": user.email} for user in users]
    return jsonify(user_list)

@main.route('/auction')
def auction():
    return render_template('auction.html')

from .models import Auction

@main.route('/create_test_spaces')
def create_test_spaces():
    # Crear 16 espacios con una subasta activa para cada uno
    for i in range(16):
        test_space = Space(position_x=i % 4, position_y=i // 4, size="small", status="available")
        db.session.add(test_space)
        db.session.commit()
        
        # Crear una subasta para cada espacio
        test_auction = Auction(
            space_id=test_space.id,
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow() + timedelta(minutes=10)
        )
        db.session.add(test_auction)
        db.session.commit()
    
    return jsonify({"message": "16 espacios y subastas de prueba creados"})

@main.route('/get_spaces_info')
def get_spaces_info():
    spaces_data = []
    spaces = Space.query.all()
    
    # Definimos un número fijo de columnas (por ejemplo, 4) y calculamos las posiciones
    columns = 4  # Ajusta según tu cuadrícula real
    for index, space in enumerate(spaces):
        # Convertimos el índice en etiquetas como A1, B1, etc.
        row_label = chr(65 + (index // columns))  # Genera A, B, C, etc.
        col_label = (index % columns) + 1         # Genera 1, 2, 3, 4, etc.
        position = f"{row_label}{col_label}"      # Combina para obtener A1, B2, etc.

        # Obtener la subasta y la puja más alta asociada
        auction = Auction.query.filter_by(space_id=space.id).order_by(Auction.start_time.desc()).first()
        highest_bid = db.session.query(db.func.max(Bid.amount)).filter(Bid.auction_id == auction.id).scalar() if auction else 0.0
        highest_bidder = db.session.query(User.name).join(Bid).filter(Bid.auction_id == auction.id, Bid.amount == highest_bid).scalar() if auction and highest_bid else None

        spaces_data.append({
            'space_id': space.id,
            'position': position,  # Etiqueta única como A1, B2, etc.
            'size': space.size,
            'status': space.status,
            'current_bid': highest_bid or 0.0,
            'highest_bidder': highest_bidder or 'Ninguno',
            'start_time': auction.start_time if auction else None,
            'end_time': auction.end_time if auction else None,
        })

    return jsonify(spaces_data)





