"""feat: add security events, products, purchases, subscriptions

Revision ID: b1c2d3e4f5a6
Revises: a13dd38bead7
Create Date: 2026-03-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, None] = 'a13dd38bead7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── security_events ──────────────────────────────────────────────────────
    op.create_table(
        'security_events',
        sa.Column('id',         sa.Integer(),               nullable=False),
        sa.Column('event_type', sa.String(),                nullable=False),
        sa.Column('severity',   sa.String(),                nullable=False),
        sa.Column('ip_address', sa.String(),                nullable=True),
        sa.Column('path',       sa.String(),                nullable=True),
        sa.Column('method',     sa.String(),                nullable=True),
        sa.Column('user_agent', sa.String(),                nullable=True),
        sa.Column('details',    sa.JSON(),                  nullable=True),
        sa.Column('user_id',    sa.Integer(),               nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_security_events_id',         'security_events', ['id'],         unique=False)
    op.create_index('ix_security_events_event_type', 'security_events', ['event_type'], unique=False)
    op.create_index('ix_security_events_severity',   'security_events', ['severity'],   unique=False)
    op.create_index('ix_security_events_ip_address', 'security_events', ['ip_address'], unique=False)
    op.create_index('ix_security_events_created_at', 'security_events', ['created_at'], unique=False)

    # ── products ─────────────────────────────────────────────────────────────
    op.create_table(
        'products',
        sa.Column('id',              sa.Integer(),               nullable=False),
        sa.Column('name',            sa.String(),                nullable=False),
        sa.Column('slug',            sa.String(),                nullable=False),
        sa.Column('description',     sa.Text(),                  nullable=True),
        sa.Column('price_cents',     sa.Integer(),               nullable=False),
        sa.Column('currency',        sa.String(3),               nullable=False, server_default='eur'),
        sa.Column('stripe_price_id', sa.String(),                nullable=True),
        sa.Column('file_path',       sa.String(),                nullable=True),
        sa.Column('cover_image',     sa.String(),                nullable=True),
        sa.Column('is_active',       sa.Boolean(),               nullable=False, server_default=sa.text('true')),
        sa.Column('created_at',      sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at',      sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug'),
    )
    op.create_index('ix_products_id',   'products', ['id'],   unique=False)
    op.create_index('ix_products_slug', 'products', ['slug'], unique=True)

    # ── purchases ────────────────────────────────────────────────────────────
    op.create_table(
        'purchases',
        sa.Column('id',                    sa.Integer(),               nullable=False),
        sa.Column('user_id',               sa.Integer(),               nullable=True),
        sa.Column('product_id',            sa.Integer(),               nullable=True),
        sa.Column('email',                 sa.String(),                nullable=False),
        sa.Column('stripe_session_id',     sa.String(),                nullable=True),
        sa.Column('stripe_payment_intent', sa.String(),                nullable=True),
        sa.Column('amount_paid_cents',     sa.Integer(),               nullable=True),
        sa.Column('currency',              sa.String(3),               nullable=True),
        sa.Column('download_token',        sa.String(),                nullable=True),
        sa.Column('download_count',        sa.Integer(),               nullable=False, server_default=sa.text('0')),
        sa.Column('max_downloads',         sa.Integer(),               nullable=False, server_default=sa.text('5')),
        sa.Column('token_expires_at',      sa.DateTime(timezone=True), nullable=True),
        sa.Column('fulfilled_at',          sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at',            sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'],    ['users.id'],    ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('stripe_session_id'),
        sa.UniqueConstraint('download_token'),
    )
    op.create_index('ix_purchases_id',               'purchases', ['id'],               unique=False)
    op.create_index('ix_purchases_user_id',          'purchases', ['user_id'],          unique=False)
    op.create_index('ix_purchases_product_id',       'purchases', ['product_id'],       unique=False)
    op.create_index('ix_purchases_stripe_session_id','purchases', ['stripe_session_id'],unique=True)
    op.create_index('ix_purchases_download_token',   'purchases', ['download_token'],   unique=True)
    op.create_index('ix_purchases_created_at',       'purchases', ['created_at'],       unique=False)

    # ── subscriptions ────────────────────────────────────────────────────────
    op.create_table(
        'subscriptions',
        sa.Column('id',                     sa.Integer(),               nullable=False),
        sa.Column('user_id',                sa.Integer(),               nullable=False),
        sa.Column('stripe_subscription_id', sa.String(),                nullable=False),
        sa.Column('stripe_customer_id',     sa.String(),                nullable=False),
        sa.Column('stripe_price_id',        sa.String(),                nullable=True),
        sa.Column('status',                 sa.String(),                nullable=False, server_default='active'),
        sa.Column('current_period_end',     sa.DateTime(timezone=True), nullable=True),
        sa.Column('trial_end',              sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancelled_at',           sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at',             sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at',             sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('stripe_subscription_id'),
        sa.UniqueConstraint('user_id'),
    )
    op.create_index('ix_subscriptions_id',                     'subscriptions', ['id'],                     unique=False)
    op.create_index('ix_subscriptions_user_id',                'subscriptions', ['user_id'],                unique=True)
    op.create_index('ix_subscriptions_stripe_subscription_id', 'subscriptions', ['stripe_subscription_id'], unique=True)
    op.create_index('ix_subscriptions_stripe_customer_id',     'subscriptions', ['stripe_customer_id'],     unique=False)


def downgrade() -> None:
    op.drop_table('subscriptions')
    op.drop_table('purchases')
    op.drop_table('products')
    op.drop_table('security_events')
