"""Initial migration after reset

Revision ID: c8e7a7685f25
Revises: 
Create Date: 2024-11-11 23:10:37.464994

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c8e7a7685f25'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('spaces',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('position_x', sa.Integer(), nullable=False),
    sa.Column('position_y', sa.Integer(), nullable=False),
    sa.Column('size', sa.String(length=20), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('sponsor', sa.String(length=120), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=50), nullable=False),
    sa.Column('email', sa.String(length=120), nullable=False),
    sa.Column('password', sa.String(length=128), nullable=False),
    sa.Column('is_admin', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    op.create_table('auctions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('space_id', sa.Integer(), nullable=False),
    sa.Column('start_time', sa.DateTime(), nullable=False),
    sa.Column('end_time', sa.DateTime(), nullable=False),
    sa.Column('highest_bidder_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['highest_bidder_id'], ['users.id'], name='fk_auction_user'),
    sa.ForeignKeyConstraint(['space_id'], ['spaces.id'], name='fk_auction_space'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('bids',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('amount', sa.Float(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('auction_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['auction_id'], ['auctions.id'], name='fk_bid_auction'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_bid_user'),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('bids')
    op.drop_table('auctions')
    op.drop_table('users')
    op.drop_table('spaces')
    # ### end Alembic commands ###