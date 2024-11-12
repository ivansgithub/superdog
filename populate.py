from datetime import datetime, timedelta
from app import create_app, db
from app.models import Space, Auction

app = create_app()

with app.app_context():
    # Limpiar las tablas de espacios y subastas antes de insertar nuevos datos, si es necesario
    db.session.query(Auction).delete()
    db.session.query(Space).delete()
    
    # Crear una cuadrícula de 3 filas x 4 columnas de espacios y subastas
    espacios = []
    for x in range(3):  # Filas (A, B, C)
        for y in range(4):  # Columnas (1, 2, 3, 4)
            # Crear el espacio
            espacio = Space(position_x=x, position_y=y, size='small', status='available')
            db.session.add(espacio)
            db.session.flush()  # Obtener el ID del espacio antes de crear la subasta
            
            # Crear una subasta para este espacio con una duración de 10 minutos
            subasta = Auction(
                space_id=espacio.id,
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow() + timedelta(minutes=10),
            
                highest_bidder_id=None
            )
            db.session.add(subasta)

    db.session.commit()
    print("Datos de espacios y subastas cargados exitosamente.")


