from flask import Flask
from .config import Config
from .extensions import db, socketio
from flask_migrate import Migrate
from apscheduler.schedulers.background import BackgroundScheduler
from .auction_tasks import check_auctions
from .routes import main 

migrate = Migrate()
scheduler = BackgroundScheduler()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.register_blueprint(main)

    # Inicializar extensiones
    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app)

    # Verifica si el `scheduler` ya está iniciado antes de comenzar y programar tareas
    if not scheduler.running:
        scheduler.add_job(func=lambda: check_auctions(app), trigger="interval", seconds=60)
        scheduler.start()

    # Cerrar el scheduler al apagar la app
    @app.teardown_appcontext
    def shutdown_scheduler(exception=None):
        # Verifica si el `scheduler` está activo antes de intentar detenerlo
        if scheduler.running:
            scheduler.shutdown()

    return app


