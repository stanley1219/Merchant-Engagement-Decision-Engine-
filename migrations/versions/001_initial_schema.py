"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2026-01-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "btree_gin"')

    op.create_table(
        "merchants",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("address", sa.Text, nullable=True),
        sa.Column("locality", sa.String(100), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("state", sa.String(100), nullable=True),
        sa.Column("identity", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("performance_metrics", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("offers", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("settings", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("version", sa.Integer, nullable=False, default=1),
        sa.Column("last_context_update", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, default=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("phone", name="uq_merchant_phone"),
    )

    op.create_index("ix_merchants_category", "merchants", ["category"])
    op.create_index("ix_merchants_category_locality", "merchants", ["category", "locality"])
    op.create_index("ix_merchants_version", "merchants", ["version"])

    op.create_table(
        "customers",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("merchant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("external_id", sa.String(100), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("profile", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("consent_flags", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("tags", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("last_interaction_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_visit_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("lifetime_value", sa.Float, nullable=False, default=0.0),
        sa.Column("visit_count", sa.Integer, nullable=False, default=0),
        sa.Column("is_active", sa.Boolean, nullable=False, default=True),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_customers_merchant_id", "customers", ["merchant_id"])
    op.create_index("ix_customers_merchant_phone", "customers", ["merchant_id", "phone"])
    op.create_index("ix_customers_merchant_external", "customers", ["merchant_id", "external_id"])
    op.create_index("ix_customers_last_visit", "customers", ["last_visit_at"])

    op.create_table(
        "triggers",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("merchant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("payload", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("priority", sa.Integer, nullable=False, default=50),
        sa.Column("source", sa.String(50), nullable=False, default="system"),
        sa.Column("status", sa.String(20), nullable=False, default="pending"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.String(500), nullable=True),
        sa.Column("retry_count", sa.Integer, nullable=False, default=0),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_triggers_merchant_id", "triggers", ["merchant_id"])
    op.create_index("ix_triggers_merchant_status", "triggers", ["merchant_id", "status"])
    op.create_index("ix_triggers_type_status", "triggers", ["type", "status"])
    op.create_index("ix_triggers_customer_id", "triggers", ["customer_id"])
    op.create_index("ix_triggers_expires", "triggers", ["expires_at"])

    op.create_table(
        "conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("merchant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("state", sa.String(50), nullable=False, default="open"),
        sa.Column("context", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("suppression_keys", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("message_count", sa.Integer, nullable=False, default=0),
        sa.Column("metadata", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_conversations_merchant_id", "conversations", ["merchant_id"])
    op.create_index("ix_conversations_merchant_state", "conversations", ["merchant_id", "state"])
    op.create_index("ix_conversations_customer_id", "conversations", ["customer_id"])

    op.create_table(
        "message_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("merchant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("trigger_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("signal_type", sa.String(50), nullable=False),
        sa.Column("output", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, default="sent"),
        sa.Column("delivery_status", sa.String(20), nullable=False, default="pending"),
        sa.Column("error_message", sa.String(500), nullable=True),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["trigger_id"], ["triggers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_message_logs_merchant_id", "message_logs", ["merchant_id"])
    op.create_index("ix_message_logs_merchant_sent", "message_logs", ["merchant_id", "sent_at"])
    op.create_index("ix_message_logs_trigger_id", "message_logs", ["trigger_id"])
    op.create_index("ix_message_logs_signal_type", "message_logs", ["signal_type"])


def downgrade() -> None:
    op.drop_table("message_logs")
    op.drop_table("conversations")
    op.drop_table("triggers")
    op.drop_table("customers")
    op.drop_table("merchants")