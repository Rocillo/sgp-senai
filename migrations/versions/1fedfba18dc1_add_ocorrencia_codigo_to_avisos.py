"""add ocorrencia_codigo to avisos

Revision ID: 1fedfba18dc1
Revises: 16a4317883e0
Create Date: 2026-03-31 21:21:04.805164

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "1fedfba18dc1"
down_revision = "16a4317883e0"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("avisos", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("ocorrencia_codigo", sa.String(length=30), nullable=True)
        )
        batch_op.create_index(
            batch_op.f("ix_avisos_ocorrencia_codigo"),
            ["ocorrencia_codigo"],
            unique=True,
        )


def downgrade():
    with op.batch_alter_table("avisos", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_avisos_ocorrencia_codigo"))
        batch_op.drop_column("ocorrencia_codigo")
