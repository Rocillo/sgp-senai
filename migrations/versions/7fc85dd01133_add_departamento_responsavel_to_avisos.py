"""add departamento_responsavel to avisos

Revision ID: 7fc85dd01133
Revises: 1fedfba18dc1
Create Date: 2026-04-07 18:10:20.935362

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7fc85dd01133"
down_revision = "1fedfba18dc1"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("avisos", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("departamento_responsavel", sa.String(length=50), nullable=True)
        )
        batch_op.create_index(
            batch_op.f("ix_avisos_departamento_responsavel"),
            ["departamento_responsavel"],
            unique=False,
        )


def downgrade():
    with op.batch_alter_table("avisos", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_avisos_departamento_responsavel"))
        batch_op.drop_column("departamento_responsavel")
        