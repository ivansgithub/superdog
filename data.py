# create_test_data.py
from app import create_app
from app.extensions import db
from app.models import Space, User, Auction, Bid
from datetime import datetime, timedelta

app = create_app()

with app.app_context():
    # 1. Crear un usuario de prueba
    user = User(name="Johnt Doe", email="johntdoe@example.com", password="password123")
    db.session.add(user)
    db.session.commit()

    # 2. Crear un espacio de prueba
    space = Space(position_x=0, position_y=0, size="medium", status="available")
    db.session.add(space)
    db.session.commit()

    # 3. Crear una subasta de prueba asociada al espacio
    auction = Auction(
        space_id=space.id,
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow() + timedelta(minutes=10),
        highest_bidder_id=user.id  # Inicialmente, este usuario será el mejor postor
    )
    db.session.add(auction)
    db.session.commit()

    # 4. Crear una puja de prueba asociada a la subasta y al usuario
    bid = Bid(amount=100.0, timestamp=datetime.utcnow(), user_id=user.id, auction_id=auction.id)
    db.session.add(bid)
    db.session.commit()

    # Confirmar que los datos fueron agregados
    print("Usuarios en la base de datos:", User.query.all())
    print("Espacios en la base de datos:", Space.query.all())
    print("Subastas en la base de datos:", Auction.query.all())
    print("Pujas en la base de datos:", Bid.query.all())



