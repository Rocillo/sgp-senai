# ====================================================================
# [BLOCO] MÓDULO
# [NOME] alarmes_service
# [RESPONSABILIDADE] Gerenciar alarmes de falta de componente para indicadores de produção
# ====================================================================

from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from sqlalchemy import inspect, text

from app.models_sqla import Peca


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] _tabela_alarmes_existe
# [RESPONSABILIDADE] Verificar existência da tabela de alarmes de componentes
# ====================================================================
def _tabela_alarmes_existe() -> bool:
    from app import db

    return inspect(db.engine).has_table("gp_component_alarm")


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] registrar_alarmes_falta_componentes
# [RESPONSABILIDADE] Abrir ocorrências de falta de componente para alimentar indicadores gerenciais
# ====================================================================
def registrar_alarmes_falta_componentes(
    session,
    modelo: str,
    codigo_conjunto: str,
    referencia: str,
    bancada_logica: str,
    faltas: List,
    origem: str = "montagem_api",
) -> None:
    if not _tabela_alarmes_existe():
        return

    agora = datetime.utcnow()

    for falta in faltas:
        codigo_peca = getattr(falta, "codigo_peca", None)
        necessario = getattr(falta, "necessario", None)
        disponivel = getattr(falta, "disponivel", None)

        if not codigo_peca:
            continue

        peca = (
            session.query(Peca)
            .filter(Peca.codigo_pneumark == codigo_peca)
            .one_or_none()
        )

        component_desc = peca.descricao if peca else None

        session.execute(
            text("""
                INSERT INTO gp_component_alarm (
                    occurred_at,
                    resolved_at,
                    bench_id,
                    modelo,
                    serial,
                    component_code,
                    component_desc,
                    required_qty,
                    available_qty,
                    downtime_min,
                    status,
                    source,
                    details_json
                )
                VALUES (
                    :occurred_at,
                    NULL,
                    :bench_id,
                    :modelo,
                    :serial,
                    :component_code,
                    :component_desc,
                    :required_qty,
                    :available_qty,
                    NULL,
                    'open',
                    :source,
                    :details_json
                )
                """),
            {
                "occurred_at": agora,
                "bench_id": bancada_logica,
                "modelo": modelo,
                "serial": referencia,
                "component_code": codigo_peca,
                "component_desc": component_desc,
                "required_qty": necessario,
                "available_qty": disponivel,
                "source": origem,
                "details_json": (
                    f'{{"codigo_conjunto":"{codigo_conjunto}",'
                    f'"referencia":"{referencia}"}}'
                ),
            },
        )


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] reconciliar_alarmes_abertos_por_componente
# [RESPONSABILIDADE] Encerrar alarmes abertos quando estoque reposto eliminar bloqueio
# ====================================================================
def reconciliar_alarmes_abertos_por_componente(
    session,
    codigo_peca: str,
    estoque_atual: int,
) -> None:
    if not codigo_peca or not _tabela_alarmes_existe():
        return

    sql_busca = """
    SELECT
        id,
        occurred_at,
        required_qty
    FROM gp_component_alarm
    WHERE component_code = :codigo_peca
      AND status = 'open'
    ORDER BY occurred_at ASC
    """

    alarmes = (
        session.execute(
            text(sql_busca),
            {"codigo_peca": codigo_peca},
        )
        .mappings()
        .all()
    )

    agora = datetime.utcnow()

    for alarme in alarmes:
        required_qty = int(alarme["required_qty"] or 0)

        if estoque_atual < required_qty:
            continue

        occurred_at = alarme["occurred_at"]

        if isinstance(occurred_at, str):
            try:
                occurred_at_dt = datetime.fromisoformat(occurred_at)
            except ValueError:
                occurred_at_dt = agora
        else:
            occurred_at_dt = occurred_at

        downtime_min = round((agora - occurred_at_dt).total_seconds() / 60, 2)

        session.execute(
            text("""
                UPDATE gp_component_alarm
                SET
                    resolved_at = :resolved_at,
                    downtime_min = :downtime_min,
                    status = 'resolved'
                WHERE id = :id
                """),
            {
                "resolved_at": agora,
                "downtime_min": downtime_min,
                "id": alarme["id"],
            },
        )


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] listar_historico_alarmes_componentes
# [RESPONSABILIDADE] Serializar histórico operacional de alarmes por falta de componente
# ====================================================================
def listar_historico_alarmes_componentes(
    session,
    data_inicio,
    data_fim,
    limite: int = 500,
) -> List[Dict]:
    if not _tabela_alarmes_existe():
        return []

    sql = """
    SELECT
        occurred_at,
        resolved_at,
        bench_id,
        modelo,
        serial,
        component_code,
        COALESCE(component_desc, component_code) AS component_label,
        required_qty,
        available_qty,
        downtime_min,
        status,
        source
    FROM gp_component_alarm
    WHERE DATE(occurred_at) BETWEEN :data_inicio AND :data_fim
    ORDER BY occurred_at DESC
    LIMIT :limite
    """

    rows = (
        session.execute(
            text(sql),
            {
                "data_inicio": data_inicio.isoformat(),
                "data_fim": data_fim.isoformat(),
                "limite": limite,
            },
        )
        .mappings()
        .all()
    )

    return [dict(row) for row in rows]


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] montar_pareto_componentes
# [RESPONSABILIDADE] Montar top 5 componentes por downtime e percentual acumulado
# ====================================================================
def montar_pareto_componentes(session, data_inicio, data_fim) -> List[Dict]:
    if not _tabela_alarmes_existe():
        return []

    sql = """
    SELECT
        COALESCE(component_desc, component_code) AS component_label,
        COUNT(*) AS alarm_count,
        ROUND(SUM(COALESCE(downtime_min, 0)), 2) AS downtime_min
    FROM gp_component_alarm
    WHERE DATE(occurred_at) BETWEEN :data_inicio AND :data_fim
    GROUP BY COALESCE(component_desc, component_code)
    ORDER BY downtime_min DESC, alarm_count DESC
    LIMIT 5
    """

    rows = (
        session.execute(
            text(sql),
            {
                "data_inicio": data_inicio.isoformat(),
                "data_fim": data_fim.isoformat(),
            },
        )
        .mappings()
        .all()
    )

    total = sum(float(row["downtime_min"] or 0) for row in rows) or 1
    acumulado = 0
    pareto = []

    for row in rows:
        downtime = float(row["downtime_min"] or 0)
        acumulado += downtime

        pareto.append(
            {
                "component_label": row["component_label"],
                "alarm_count": int(row["alarm_count"]),
                "downtime_min": downtime,
                "cum_pct": round((acumulado / total) * 100, 2),
            }
        )

    return pareto


# ====================================================================
# MAPA DO ARQUIVO
# --------------------------------------------------------------------
# FUNÇÃO: registrar_alarmes_falta_componentes
# FUNÇÃO: reconciliar_alarmes_abertos_por_componente
# FUNÇÃO: listar_historico_alarmes_componentes
# FUNÇÃO: montar_pareto_componentes
# ====================================================================
