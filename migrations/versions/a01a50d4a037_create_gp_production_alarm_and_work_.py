"""create gp production alarm and work calendar

Revision ID: a01a50d4a037
Revises: 7fc85dd01133
Create Date: 2026-05-22 16:54:45.004308

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a01a50d4a037"
down_revision = "7fc85dd01133"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "gp_component_alarm",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("bench_id", sa.String(length=10), nullable=False),
        sa.Column("modelo", sa.String(length=50), nullable=False),
        sa.Column("serial", sa.String(length=64), nullable=True),
        sa.Column("component_code", sa.String(length=50), nullable=False),
        sa.Column("component_desc", sa.String(length=120), nullable=True),
        sa.Column("required_qty", sa.Integer(), nullable=True),
        sa.Column("available_qty", sa.Integer(), nullable=True),
        sa.Column("downtime_min", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="open"),
        sa.Column(
            "source",
            sa.String(length=30),
            nullable=False,
            server_default="montagem_api",
        ),
        sa.Column("details_json", sa.JSON(), nullable=True),
    )

    op.create_index(
        "ix_gp_component_alarm_occurred_at",
        "gp_component_alarm",
        ["occurred_at"],
    )
    op.create_index(
        "ix_gp_component_alarm_modelo",
        "gp_component_alarm",
        ["modelo"],
    )
    op.create_index(
        "ix_gp_component_alarm_component_code",
        "gp_component_alarm",
        ["component_code"],
    )
    op.create_index(
        "ix_gp_component_alarm_status",
        "gp_component_alarm",
        ["status"],
    )

    op.create_table(
        "work_calendar",
        sa.Column("dia", sa.Date(), primary_key=True),
        sa.Column("eh_dia_util", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("descricao", sa.String(length=120), nullable=True),
        sa.Column(
            "turno_minutos_planejados",
            sa.Integer(),
            nullable=False,
            server_default="480",
        ),
    )

    op.create_index(
        "ix_work_calendar_eh_dia_util",
        "work_calendar",
        ["eh_dia_util"],
    )


def downgrade():
    op.drop_index("ix_work_calendar_eh_dia_util", table_name="work_calendar")
    op.drop_table("work_calendar")

    op.drop_index("ix_gp_component_alarm_status", table_name="gp_component_alarm")
    op.drop_index(
        "ix_gp_component_alarm_component_code",
        table_name="gp_component_alarm",
    )
    op.drop_index("ix_gp_component_alarm_modelo", table_name="gp_component_alarm")
    op.drop_index(
        "ix_gp_component_alarm_occurred_at",
        table_name="gp_component_alarm",
    )
    op.drop_table("gp_component_alarm")