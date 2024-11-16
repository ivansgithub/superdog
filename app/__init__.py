from flask import Flask
from .config import Config
from .extensions import db, socketio
from flask_migrate import Migrate
from apscheduler.schedulers.background import BackgroundScheduler
from .auction_tasks import check_auctions
from .routes import main
from flask_login import LoginManager
from .models import User
from .routes import auth_bp

migrate = Migrate()
scheduler = BackgroundScheduler()
login_manager = LoginManager()  # Instancia de LoginManager

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.register_blueprint(main)
    app.register_blueprint(auth_bp, url_prefix='') 

    # Inicializar extensiones
    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app)
    login_manager.init_app(app)  # Inicializar LoginManager con la app
    login_manager.login_view = 'main.login' 
    login_manager.login_view = 'auth.login'
    # Función para cargar el usuario
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Programación del scheduler de tareas, solo si no está activo
    if not scheduler.running:
        scheduler.add_job(func=lambda: check_auctions(app), trigger="interval", seconds=60)
        scheduler.start()

    # Cerrar el scheduler al apagar la app
    @app.teardown_appcontext
    def shutdown_scheduler(exception=None):
        if scheduler.running:
            try:
                scheduler.shutdown(wait=False)
            except RuntimeError:
                pass 

    return app


