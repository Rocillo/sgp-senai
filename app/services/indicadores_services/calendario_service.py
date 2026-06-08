# ====================================================================
# [BLOCO] MÓDULO
# [NOME] calendario_service
# [RESPONSABILIDADE] Calcular dias produtivos e ociosos a partir do calendário operacional
# ====================================================================

from __future__ import annotations

from datetime import date, datetime
from typing import Dict, List, Set

from sqlalchemy import inspect, text

from app import db
from app.services.indicadores_services.periodo_service import dias_uteis_fallback


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] _tabela_calendario_existe
# [RESPONSABILIDADE] Verificar existência da tabela de calendário operacional
# ====================================================================
def _tabela_calendario_existe() -> bool:
    return inspect(db.engine).has_table("work_calendar")


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] obter_dias_uteis_operacionais
# [RESPONSABILIDADE] Obter dias úteis pela tabela oficial ou fallback segunda-sexta
# ====================================================================
def obter_dias_uteis_operacionais(data_inicio: date, data_fim: date) -> List[date]:
    if not _tabela_calendario_existe():
        return dias_uteis_fallback(data_inicio, data_fim)

    sql = """
    SELECT dia
    FROM work_calendar
    WHERE dia BETWEEN :data_inicio AND :data_fim
      AND eh_dia_util = 1
    ORDER BY dia
    """

    rows = db.session.execute(
        text(sql),
        {
            "data_inicio": data_inicio.isoformat(),
            "data_fim": data_fim.isoformat(),
        },
    ).fetchall()

    return [datetime.strptime(str(row[0]), "%Y-%m-%d").date() for row in rows]


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] obter_dias_com_producao_real
# [RESPONSABILIDADE] Obter dias com início ou fim de etapa registrado
# ====================================================================
def obter_dias_com_producao_real(data_inicio: date, data_fim: date) -> Set[str]:
    dialeto = db.session.bind.dialect.name

    if dialeto == "postgresql":
        sql = """
        SELECT DISTINCT dia
        FROM (
            SELECT started_at::date AS dia
            FROM gp_work_stage
            WHERE started_at IS NOT NULL

            UNION

            SELECT finished_at::date AS dia
            FROM gp_work_stage
            WHERE finished_at IS NOT NULL
        ) x
        WHERE dia BETWEEN :data_inicio AND :data_fim
        ORDER BY dia
        """
    else:
        sql = """
        SELECT DISTINCT dia
        FROM (
            SELECT DATE(started_at) AS dia
            FROM gp_work_stage
            WHERE started_at IS NOT NULL

            UNION

            SELECT DATE(finished_at) AS dia
            FROM gp_work_stage
            WHERE finished_at IS NOT NULL
        ) x
        WHERE dia BETWEEN :data_inicio AND :data_fim
        ORDER BY dia
        """

    rows = db.session.execute(
        text(sql),
        {
            "data_inicio": data_inicio.isoformat(),
            "data_fim": data_fim.isoformat(),
        },
    ).fetchall()

    return {str(row[0]) for row in rows}


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] _weekday_ptbr
# [RESPONSABILIDADE] Converter dia da semana para PT-BR
# ====================================================================
def _weekday_ptbr(dia: date) -> str:
    nomes = {
        0: "Segunda-feira",
        1: "Terça-feira",
        2: "Quarta-feira",
        3: "Quinta-feira",
        4: "Sexta-feira",
        5: "Sábado",
        6: "Domingo",
    }

    return nomes[dia.weekday()]


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] montar_indicador_ociosidade
# [RESPONSABILIDADE] Cruzar calendário operacional com produção real e retornar dias produtivos/ociosos
# ====================================================================
def montar_indicador_ociosidade(data_inicio: date, data_fim: date) -> Dict:
    dias_uteis = obter_dias_uteis_operacionais(data_inicio, data_fim)
    dias_ativos = obter_dias_com_producao_real(data_inicio, data_fim)

    dias_produtivos = [dia for dia in dias_uteis if dia.isoformat() in dias_ativos]
    dias_ociosos = [dia for dia in dias_uteis if dia.isoformat() not in dias_ativos]

    base = len(dias_uteis) or 1

    return {
        "dias_produtivos": len(dias_produtivos),
        "dias_ociosos": len(dias_ociosos),
        "taxa_ociosidade_pct": round((len(dias_ociosos) / base) * 100, 2),
        "dias_sem_montagem": [
            {
                "dia": dia.isoformat(),
                "weekday": _weekday_ptbr(dia),
            }
            for dia in dias_ociosos
        ],
    }


# ====================================================================
# MAPA DO ARQUIVO
# --------------------------------------------------------------------
# FUNÇÃO: obter_dias_uteis_operacionais
# FUNÇÃO: obter_dias_com_producao_real
# FUNÇÃO: montar_indicador_ociosidade
# ====================================================================
