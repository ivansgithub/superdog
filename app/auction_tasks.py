# auction_tasks.py
from datetime import datetime
from .models import Auction, Space, Bid
from .extensions import db, socketio

def check_auctions(app):
    with app.app_context():
        expired_auctions = Auction.query.filter(
            Auction.end_time < datetime.utcnow(),
            Auction.highest_bidder_id != None
        ).all()

        for auction in expired_auctions:
            space = auction.space
            
            highest_bid = db.session.query(db.func.max(Bid.amount)).filter(Bid.auction_id == auction.id).scalar()
            
            if highest_bid:
                socketio.emit('space_reserved', {
                    'space_id': auction.space_id,
                    'user_id': auction.highest_bidder_id,
                    'final_bid': highest_bid
                }, to='/', include_self=True)
                
                space.status = 'reserved'
                db.session.commit()

        return "Subastas verificadas y cerradas."
