"""create avisos tables

Revision ID: 16a4317883e0
Revises: 3cf93bffeffe
Create Date: 2026-03-31 15:47:34.014667

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "16a4317883e0"
down_revision = "3cf93bffeffe"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "avisos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("codigo", sa.String(length=80), nullable=False),
        sa.Column("tipo", sa.String(length=50), nullable=False),
        sa.Column("titulo", sa.String(length=255), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=False),
        sa.Column("severidade", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("modelo", sa.String(length=50), nullable=True),
        sa.Column("origem", sa.String(length=80), nullable=True),
        sa.Column("data_aviso", sa.DateTime(), nullable=False),
        sa.Column("capacidade_atual", sa.Integer(), nullable=True),
        sa.Column("estoque_maximo", sa.Integer(), nullable=True),
        sa.Column("lido_por_user_id", sa.Integer(), nullable=True),
        sa.Column("lido_por_nome", sa.String(length=120), nullable=True),
        sa.Column("lido_em", sa.DateTime(), nullable=True),
        sa.Column("resolvido_por_user_id", sa.Integer(), nullable=True),
        sa.Column("resolvido_por_nome", sa.String(length=120), nullable=True),
        sa.Column("resolvido_em", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    with op.batch_alter_table("avisos", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_avisos_codigo"), ["codigo"], unique=True)
        batch_op.create_index(batch_op.f("ix_avisos_modelo"), ["modelo"], unique=False)

    op.create_table(
        "avisos_destinatarios",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("aviso_id", sa.Integer(), nullable=False),
        sa.Column("setor", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("comunicado_por_user_id", sa.Integer(), nullable=True),
        sa.Column("comunicado_por_nome", sa.String(length=120), nullable=True),
        sa.Column("comunicado_em", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["aviso_id"], ["avisos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("aviso_id", "setor", name="uq_aviso_destinatario_setor"),
    )

    with op.batch_alter_table("avisos_destinatarios", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_avisos_destinatarios_aviso_id"), ["aviso_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_avisos_destinatarios_setor"), ["setor"], unique=False
        )

    op.create_table(
        "avisos_eventos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("aviso_id", sa.Integer(), nullable=False),
        sa.Column("tipo_evento", sa.String(length=30), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("usuario_nome", sa.String(length=120), nullable=True),
        sa.Column("destino", sa.String(length=50), nullable=True),
        sa.Column("observacao", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["aviso_id"], ["avisos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    with op.batch_alter_table("avisos_eventos", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_avisos_eventos_aviso_id"), ["aviso_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_avisos_eventos_tipo_evento"), ["tipo_evento"], unique=False
        )


def downgrade():
    with op.batch_alter_table("avisos_eventos", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_avisos_eventos_tipo_evento"))
        batch_op.drop_index(batch_op.f("ix_avisos_eventos_aviso_id"))

    op.drop_table("avisos_eventos")

    with op.batch_alter_table("avisos_destinatarios", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_avisos_destinatarios_setor"))
        batch_op.drop_index(batch_op.f("ix_avisos_destinatarios_aviso_id"))

    op.drop_table("avisos_destinatarios")

    with op.batch_alter_table("avisos", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_avisos_modelo"))
        batch_op.drop_index(batch_op.f("ix_avisos_codigo"))

    op.drop_table("avisos")
