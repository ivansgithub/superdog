from datetime import datetime, timedelta
from .extensions import db

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    bids = db.relationship('Bid', backref='user', lazy=True)
    auctions = db.relationship('Auction', backref='highest_bidder', lazy=True)
    

class Space(db.Model):
    __tablename__ = 'spaces'
    id = db.Column(db.Integer, primary_key=True)
    position_x = db.Column(db.Integer, nullable=False)
    position_y = db.Column(db.Integer, nullable=False)
    size = db.Column(db.String(20), nullable=False)  # Ejemplo: "small", "medium", "large"
    status = db.Column(db.String(20), default="available")  # "available", "in auction", "reserved"
    sponsor = db.Column(db.String(120), nullable=True)

    auctions = db.relationship('Auction', backref='space', lazy=True)  # Todas las subastas de un espacio

class Bid(db.Model):
    __tablename__ = 'bids'
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', name="fk_bid_user"), nullable=False)
    auction_id = db.Column(db.Integer, db.ForeignKey('auctions.id', name="fk_bid_auction"), nullable=False)

class Auction(db.Model):
    __tablename__ = 'auctions'
    id = db.Column(db.Integer, primary_key=True)
    space_id = db.Column(db.Integer, db.ForeignKey('spaces.id', name="fk_auction_space"), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=False)
    highest_bidder_id = db.Column(db.Integer, db.ForeignKey('users.id', name="fk_auction_user"), nullable=True)

    bids = db.relationship('Bid', backref='auction', lazy=True)

    # Método para establecer la duración de la subasta
    def set_end_time(self, duration_minutes=10):
        self.end_time = self.start_time + timedelta(minutes=duration_minutes)
