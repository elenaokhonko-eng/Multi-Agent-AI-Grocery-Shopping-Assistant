"""Canonical Schema - ADR-001

Revision ID: 0001_canonical_schema
Revises: 
Create Date: 2026-08-28 21:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlmodel import Column, JSON

# revision identifiers, used by Alembic.
revision: str = '0001_canonical_schema'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. shopping_lists
    op.create_table(
        'shopping_lists',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_shopping_lists_name'), 'shopping_lists', ['name'], unique=False)

    # 2. shopping_list_items
    op.create_table(
        'shopping_list_items',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('shopping_list_id', sa.Uuid(), nullable=False),
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('category', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('desired_quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('unit_measure', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default='pack'),
        sa.Column('min_pack_size', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('max_pack_size', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('must_have', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('substitution_policy', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default='SAME_BRAND_ONLY'),
        sa.Column('preferred_brands', sa.JSON(), nullable=True),
        sa.Column('exclusions', sa.JSON(), nullable=True),
        sa.Column('pinned_skus', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['shopping_list_id'], ['shopping_lists.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_shopping_list_items_shopping_list_id'), 'shopping_list_items', ['shopping_list_id'], unique=False)

    # 3. comparison_snapshots
    op.create_table(
        'comparison_snapshots',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('shopping_list_id', sa.Uuid(), nullable=False),
        sa.Column('list_version', sa.Integer(), nullable=False),
        sa.Column('frozen_items_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['shopping_list_id'], ['shopping_lists.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_comparison_snapshots_shopping_list_id'), 'comparison_snapshots', ['shopping_list_id'], unique=False)

    # 4. comparison_runs
    op.create_table(
        'comparison_runs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('snapshot_id', sa.Uuid(), nullable=False),
        sa.Column('status', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default='QUEUED'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['snapshot_id'], ['comparison_snapshots.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_comparison_runs_snapshot_id'), 'comparison_runs', ['snapshot_id'], unique=False)
    op.create_index(op.f('ix_comparison_runs_status'), 'comparison_runs', ['status'], unique=False)

    # 5. store_quotes
    op.create_table(
        'store_quotes',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('run_id', sa.Uuid(), nullable=False),
        sa.Column('retailer_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('retailer_cart_id', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('cart_url', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('cart_fingerprint', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('subtotal_cents', sa.Integer(), nullable=False),
        sa.Column('promotions_discount_cents', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('delivery_fee_cents', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('service_fee_cents', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('bag_fee_cents', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('slot_fee_cents', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('gross_total_cents', sa.Integer(), nullable=False),
        sa.Column('derived_net_cents', sa.Integer(), nullable=False),
        sa.Column('gst_cents', sa.Integer(), nullable=False),
        sa.Column('free_delivery_threshold_cents', sa.Integer(), nullable=True),
        sa.Column('amount_needed_for_free_delivery_cents', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_complete', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('missing_must_have_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('selected_delivery_slot_id', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('selected_delivery_slot_window', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['run_id'], ['comparison_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_store_quotes_run_id'), 'store_quotes', ['run_id'], unique=False)
    op.create_index(op.f('ix_store_quotes_retailer_id'), 'store_quotes', ['retailer_id'], unique=False)
    op.create_index(op.f('ix_store_quotes_cart_fingerprint'), 'store_quotes', ['cart_fingerprint'], unique=False)

    # 6. quote_lines
    op.create_table(
        'quote_lines',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('quote_id', sa.Uuid(), nullable=False),
        sa.Column('shopping_item_id', sa.Uuid(), nullable=False),
        sa.Column('retailer_sku', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('product_title', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('product_brand', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('product_url', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('image_url', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('pack_size', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('requested_quantity', sa.Integer(), nullable=False),
        sa.Column('packs_added', sa.Integer(), nullable=False),
        sa.Column('is_in_stock', sa.Boolean(), nullable=False),
        sa.Column('is_exact_match', sa.Boolean(), nullable=False),
        sa.Column('is_substituted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('missing_reason', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('unit_price_cents', sa.Integer(), nullable=False),
        sa.Column('unit_measure', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default='pack'),
        sa.Column('line_total_cents', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['quote_id'], ['store_quotes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_quote_lines_quote_id'), 'quote_lines', ['quote_id'], unique=False)
    op.create_index(op.f('ix_quote_lines_shopping_item_id'), 'quote_lines', ['shopping_item_id'], unique=False)

    # 7. approvals
    op.create_table(
        'approvals',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('quote_id', sa.Uuid(), nullable=False),
        sa.Column('approval_token', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('idempotency_key', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('delivery_slot_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('expected_fingerprint', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('is_used', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['quote_id'], ['store_quotes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_approvals_approval_token'), 'approvals', ['approval_token'], unique=True)
    op.create_index(op.f('ix_approvals_idempotency_key'), 'approvals', ['idempotency_key'], unique=True)
    op.create_index(op.f('ix_approvals_quote_id'), 'approvals', ['quote_id'], unique=False)

    # 8. order_receipts
    op.create_table(
        'order_receipts',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('approval_id', sa.Uuid(), nullable=False),
        sa.Column('retailer_order_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('retailer_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('confirmed_total_cents', sa.Integer(), nullable=False),
        sa.Column('confirmed_delivery_slot', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('receipt_url', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('placed_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['approval_id'], ['approvals.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_order_receipts_approval_id'), 'order_receipts', ['approval_id'], unique=True)
    op.create_index(op.f('ix_order_receipts_retailer_order_id'), 'order_receipts', ['retailer_order_id'], unique=False)

    # 9. user_product_corrections
    op.create_table(
        'user_product_corrections',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('shopping_item_name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('retailer_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('preferred_sku', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('preferred_title', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_product_corrections_shopping_item_name'), 'user_product_corrections', ['shopping_item_name'], unique=False)
    op.create_index(op.f('ix_user_product_corrections_retailer_id'), 'user_product_corrections', ['retailer_id'], unique=False)


def downgrade() -> None:
    op.drop_table('user_product_corrections')
    op.drop_table('order_receipts')
    op.drop_table('approvals')
    op.drop_table('quote_lines')
    op.drop_table('store_quotes')
    op.drop_table('comparison_runs')
    op.drop_table('comparison_snapshots')
    op.drop_table('shopping_list_items')
    op.drop_table('shopping_lists')
