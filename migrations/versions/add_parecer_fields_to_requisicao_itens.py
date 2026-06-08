"""Add parecer fields to compras_requisicao_itens

Revision ID: add_parecer_fields_to_requisicao_itens
Revises: create_compras_requisicoes_tables
Create Date: 2026-06-01 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "add_parecer_fields_to_requisicao_itens"
down_revision = "create_compras_requisicoes_tables"
branch_labels = None
depends_on = None


def upgrade():
    # Adicionar campos de parecer à tabela compras_requisicao_itens
    op.add_column(
        "compras_requisicao_itens",
        sa.Column("parecer_status", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "compras_requisicao_itens",
        sa.Column("parecer_nivel", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "compras_requisicao_itens",
        sa.Column("parecer_mensagem", sa.Text(), nullable=True),
    )
    op.add_column(
        "compras_requisicao_itens",
        sa.Column("parecer_quantidade_sugerida", sa.Integer(), nullable=True),
    )
    op.add_column(
        "compras_requisicao_itens",
        sa.Column("parecer_excesso_atual", sa.Integer(), nullable=True),
    )
    op.add_column(
        "compras_requisicao_itens",
        sa.Column(
            "decisao_contra_recomendacao",
            sa.Boolean(),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade():
    # Remover campos de parecer da tabela compras_requisicao_itens
    op.drop_column("compras_requisicao_itens", "decisao_contra_recomendacao")
    op.drop_column("compras_requisicao_itens", "parecer_excesso_atual")
    op.drop_column("compras_requisicao_itens", "parecer_quantidade_sugerida")
    op.drop_column("compras_requisicao_itens", "parecer_mensagem")
    op.drop_column("compras_requisicao_itens", "parecer_nivel")
    op.drop_column("compras_requisicao_itens", "parecer_status")
