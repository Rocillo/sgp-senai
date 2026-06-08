"""Create compras requisicoes tables

Revision ID: create_compras_requisicoes_tables
Revises: afbad526ba33
Create Date: 2026-05-29 18:36:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "create_compras_requisicoes_tables"
down_revision = "a01a50d4a037"
branch_labels = None
depends_on = None


def upgrade():
    # --- 1. Criar tabela compras_requisicoes ---
    op.create_table(
        "compras_requisicoes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("numero_requisicao", sa.String(length=50), nullable=False),
        sa.Column("solicitante_id", sa.Integer(), nullable=True),
        sa.Column("solicitante_nome_snapshot", sa.String(length=100), nullable=True),
        sa.Column("setor", sa.String(length=100), nullable=True),
        sa.Column(
            "status", sa.String(length=50), nullable=False, server_default="SOLICITADA"
        ),
        sa.Column("urgencia", sa.String(length=20), nullable=True),
        sa.Column("prazo_desejado", sa.Date(), nullable=True),
        sa.Column("data_solicitacao", sa.DateTime(), nullable=False),
        sa.Column("observacao_geral", sa.Text(), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("numero_requisicao"),
    )

    # Criar índices para compras_requisicoes
    op.create_index(
        "ix_compras_requisicoes_numero_requisicao",
        "compras_requisicoes",
        ["numero_requisicao"],
    )
    op.create_index("ix_compras_requisicoes_status", "compras_requisicoes", ["status"])
    op.create_index(
        "ix_compras_requisicoes_solicitante_id",
        "compras_requisicoes",
        ["solicitante_id"],
    )
    op.create_index(
        "ix_compras_requisicoes_data_solicitacao",
        "compras_requisicoes",
        ["data_solicitacao"],
    )

    # --- 2. Criar tabela compras_requisicao_itens ---
    op.create_table(
        "compras_requisicao_itens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("requisicao_id", sa.Integer(), nullable=False),
        sa.Column("tipo_item", sa.String(length=50), nullable=False),
        sa.Column("peca_id", sa.Integer(), nullable=True),
        sa.Column("codigo_pneumark_snapshot", sa.String(length=50), nullable=True),
        sa.Column("descricao_snapshot", sa.String(length=200), nullable=True),
        sa.Column("descricao_digitada", sa.String(length=200), nullable=True),
        sa.Column("quantidade", sa.Numeric(12, 3), nullable=False),
        sa.Column("unidade", sa.String(length=20), nullable=True),
        sa.Column("estoque_atual_snapshot", sa.Numeric(12, 3), nullable=True),
        sa.Column("ultimo_preco_referencia", sa.Numeric(12, 2), nullable=True),
        sa.Column("link_referencia_principal", sa.String(length=500), nullable=True),
        sa.Column("observacao_item", sa.Text(), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["requisicao_id"],
            ["compras_requisicoes.id"],
        ),
    )

    # Criar índices para compras_requisicao_itens
    op.create_index(
        "ix_compras_requisicao_itens_requisicao_id",
        "compras_requisicao_itens",
        ["requisicao_id"],
    )
    op.create_index(
        "ix_compras_requisicao_itens_tipo_item",
        "compras_requisicao_itens",
        ["tipo_item"],
    )
    op.create_index(
        "ix_compras_requisicao_itens_peca_id", "compras_requisicao_itens", ["peca_id"]
    )

    # --- 3. Criar tabela compras_historico_status ---
    op.create_table(
        "compras_historico_status",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("requisicao_id", sa.Integer(), nullable=False),
        sa.Column("status_anterior", sa.String(length=50), nullable=True),
        sa.Column("status_novo", sa.String(length=50), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("usuario_nome_snapshot", sa.String(length=100), nullable=True),
        sa.Column("data_evento", sa.DateTime(), nullable=False),
        sa.Column("comentario", sa.Text(), nullable=True),
        sa.Column(
            "origem_evento",
            sa.String(length=50),
            nullable=False,
            server_default="sistema",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["requisicao_id"],
            ["compras_requisicoes.id"],
        ),
    )

    # Criar índices para compras_historico_status
    op.create_index(
        "ix_compras_historico_status_requisicao_id",
        "compras_historico_status",
        ["requisicao_id"],
    )
    op.create_index(
        "ix_compras_historico_status_data_evento",
        "compras_historico_status",
        ["data_evento"],
    )


def downgrade():
    # Remover tabelas na ordem inversa (devido às foreign keys)
    op.drop_index(
        "ix_compras_historico_status_data_evento", table_name="compras_historico_status"
    )
    op.drop_index(
        "ix_compras_historico_status_requisicao_id",
        table_name="compras_historico_status",
    )
    op.drop_table("compras_historico_status")

    op.drop_index(
        "ix_compras_requisicao_itens_peca_id", table_name="compras_requisicao_itens"
    )
    op.drop_index(
        "ix_compras_requisicao_itens_tipo_item", table_name="compras_requisicao_itens"
    )
    op.drop_index(
        "ix_compras_requisicao_itens_requisicao_id",
        table_name="compras_requisicao_itens",
    )
    op.drop_table("compras_requisicao_itens")

    op.drop_index(
        "ix_compras_requisicoes_data_solicitacao", table_name="compras_requisicoes"
    )
    op.drop_index(
        "ix_compras_requisicoes_solicitante_id", table_name="compras_requisicoes"
    )
    op.drop_index("ix_compras_requisicoes_status", table_name="compras_requisicoes")
    op.drop_index(
        "ix_compras_requisicoes_numero_requisicao", table_name="compras_requisicoes"
    )
    op.drop_table("compras_requisicoes")
