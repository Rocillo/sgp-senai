# ====================================================================
# [BLOCO] MÓDULO
# [NOME] indicadores_service
# [RESPONSABILIDADE] Orquestrar consultas, agregações e payload JSON dos indicadores de produção
# ====================================================================

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from math import ceil, floor
from statistics import mean
from typing import Dict, List, Tuple

from sqlalchemy import inspect, text

from app import db

MODELOS_PADRAO = ["PM2100", "PM2200", "PM700"]
LIMITE_DURACAO_PROCESSO_MIN = 16 * 60


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] parse_periodo_indicadores
# [RESPONSABILIDADE] Validar e normalizar parâmetros data_inicio e data_fim
# ====================================================================
def parse_periodo_indicadores(args) -> Tuple[date, date]:
    data_inicio_raw = args.get("data_inicio")
    data_fim_raw = args.get("data_fim")

    if not data_inicio_raw or not data_fim_raw:
        hoje = date.today()
        return hoje.replace(day=1), hoje

    try:
        data_inicio = datetime.strptime(data_inicio_raw, "%Y-%m-%d").date()
        data_fim = datetime.strptime(data_fim_raw, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("Use o formato YYYY-MM-DD para data_inicio e data_fim.")

    if data_inicio > data_fim:
        raise ValueError("data_inicio não pode ser maior que data_fim.")

    return data_inicio, data_fim


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] build_producao_indicadores_payload
# [RESPONSABILIDADE] Montar payload consolidado da API de indicadores de produção
# ====================================================================
def build_producao_indicadores_payload(data_inicio: date, data_fim: date) -> Dict:
    ordens = _buscar_ordens_finalizadas(data_inicio, data_fim)
    ordens, anomalias = _marcar_anomalias_tempo(ordens)

    ordens_validas = [ordem for ordem in ordens if not ordem["anomalia"]]

    volume = _montar_volume_mensal(ordens, data_inicio, data_fim)
    tempo_medio = _montar_tempo_medio_mensal(
        ordens_validas,
        anomalias,
        data_inicio,
        data_fim,
    )
    alarmes = _montar_alarmes_componentes(data_inicio, data_fim)
    ociosidade = _montar_ociosidade(data_inicio, data_fim)

    duracoes_validas = [ordem["duracao_min"] for ordem in ordens_validas]
    tempo_medio_geral = round(mean(duracoes_validas), 2) if duracoes_validas else None

    return {
        "ok": True,
        "periodo": {
            "data_inicio": data_inicio.isoformat(),
            "data_fim": data_fim.isoformat(),
        },
        "modelos": MODELOS_PADRAO,
        "resumo": {
            "maquinas_finalizadas": len(ordens),
            "tempo_medio_limpo_min": tempo_medio_geral,
            "anomalias_processo": len(anomalias),
            "dias_produtivos": ociosidade["dias_produtivos"],
            "dias_ociosos": ociosidade["dias_ociosos"],
            "taxa_ociosidade_pct": ociosidade["taxa_ociosidade_pct"],
        },
        "volume": volume,
        "tempo_medio": tempo_medio,
        "alarmes_componentes": alarmes,
        "ociosidade": ociosidade,
    }


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] _dialeto_banco
# [RESPONSABILIDADE] Identificar dialeto ativo do banco para montar SQL compatível
# ====================================================================
def _dialeto_banco() -> str:
    return db.engine.dialect.name


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] _buscar_ordens_finalizadas
# [RESPONSABILIDADE] Buscar ordens finalizadas com início, fim, duração e mês de referência
# ====================================================================
def _buscar_ordens_finalizadas(data_inicio: date, data_fim: date) -> List[Dict]:
    dialeto = _dialeto_banco()

    if dialeto == "postgresql":
        sql = """
        WITH order_times AS (
            SELECT
                o.id AS ordem_id,
                o.serial,
                o.modelo,
                MIN(s.started_at) AS started_at,
                COALESCE(o.finished_at, MAX(s.finished_at)) AS finished_at,
                ROUND(
                    EXTRACT(
                        EPOCH FROM (
                            COALESCE(o.finished_at, MAX(s.finished_at)) - MIN(s.started_at)
                        )
                    ) / 60.0,
                    2
                ) AS duracao_min
            FROM gp_work_order o
            JOIN gp_work_stage s ON s.order_id = o.id
            WHERE o.modelo IS NOT NULL
            GROUP BY o.id, o.serial, o.modelo, o.finished_at
            HAVING MIN(s.started_at) IS NOT NULL
               AND COALESCE(o.finished_at, MAX(s.finished_at)) IS NOT NULL
        )
        SELECT
            ordem_id,
            serial,
            modelo,
            started_at,
            finished_at,
            duracao_min,
            to_char(date_trunc('month', finished_at), 'YYYY-MM') AS mes_ref
        FROM order_times
        WHERE finished_at::date BETWEEN :data_inicio AND :data_fim
        ORDER BY finished_at
        """
    else:
        sql = """
        WITH order_times AS (
            SELECT
                o.id AS ordem_id,
                o.serial,
                o.modelo,
                MIN(s.started_at) AS started_at,
                COALESCE(o.finished_at, MAX(s.finished_at)) AS finished_at,
                ROUND(
                    (
                        julianday(COALESCE(o.finished_at, MAX(s.finished_at))) -
                        julianday(MIN(s.started_at))
                    ) * 24 * 60,
                    2
                ) AS duracao_min
            FROM gp_work_order o
            JOIN gp_work_stage s ON s.order_id = o.id
            WHERE o.modelo IS NOT NULL
            GROUP BY o.id, o.serial, o.modelo, o.finished_at
            HAVING MIN(s.started_at) IS NOT NULL
               AND COALESCE(o.finished_at, MAX(s.finished_at)) IS NOT NULL
        )
        SELECT
            ordem_id,
            serial,
            modelo,
            started_at,
            finished_at,
            duracao_min,
            strftime('%Y-%m', finished_at) AS mes_ref
        FROM order_times
        WHERE DATE(finished_at) BETWEEN :data_inicio AND :data_fim
        ORDER BY finished_at
        """

    registros = (
        db.session.execute(
            text(sql),
            {
                "data_inicio": data_inicio.isoformat(),
                "data_fim": data_fim.isoformat(),
            },
        )
        .mappings()
        .all()
    )

    ordens = []

    for row in registros:
        modelo = row["modelo"]

        if modelo not in MODELOS_PADRAO:
            continue

        ordens.append(
            {
                "ordem_id": row["ordem_id"],
                "serial": row["serial"],
                "modelo": modelo,
                "started_at": str(row["started_at"]),
                "finished_at": str(row["finished_at"]),
                "duracao_min": float(row["duracao_min"] or 0),
                "mes_ref": row["mes_ref"],
                "anomalia": False,
                "motivos_anomalia": [],
            }
        )

    return ordens


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] _quantil
# [RESPONSABILIDADE] Calcular quantil para regra IQR de anomalias
# ====================================================================
def _quantil(valores_ordenados: List[float], q: float):
    if not valores_ordenados:
        return None

    posicao = (len(valores_ordenados) - 1) * q
    baixo = floor(posicao)
    alto = ceil(posicao)

    if baixo == alto:
        return valores_ordenados[int(posicao)]

    return valores_ordenados[baixo] + (
        valores_ordenados[alto] - valores_ordenados[baixo]
    ) * (posicao - baixo)


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] _marcar_anomalias_tempo
# [RESPONSABILIDADE] Marcar tempos fora do padrão sem contaminar médias gerenciais
# ====================================================================
def _marcar_anomalias_tempo(ordens: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    duracoes_por_modelo = defaultdict(list)

    for ordem in ordens:
        if ordem["duracao_min"] > 0:
            duracoes_por_modelo[ordem["modelo"]].append(ordem["duracao_min"])

    limites_por_modelo = {}

    for modelo, duracoes in duracoes_por_modelo.items():
        duracoes = sorted(duracoes)
        q1 = _quantil(duracoes, 0.25)
        q3 = _quantil(duracoes, 0.75)

        if q1 is None or q3 is None:
            limites_por_modelo[modelo] = {"inferior": None, "superior": None}
            continue

        iqr = q3 - q1
        limites_por_modelo[modelo] = {
            "inferior": q1 - 1.5 * iqr,
            "superior": q3 + 1.5 * iqr,
        }

    anomalias = []

    for ordem in ordens:
        motivos = []
        limites = limites_por_modelo.get(ordem["modelo"], {})
        inferior = limites.get("inferior")
        superior = limites.get("superior")

        if ordem["duracao_min"] <= 0:
            motivos.append("duracao_invalida")

        if ordem["duracao_min"] > LIMITE_DURACAO_PROCESSO_MIN:
            motivos.append("limite_operacional")

        if superior is not None and ordem["duracao_min"] > superior:
            motivos.append("iqr_superior")

        if inferior is not None and ordem["duracao_min"] < inferior:
            motivos.append("iqr_inferior")

        if motivos:
            ordem["anomalia"] = True
            ordem["motivos_anomalia"] = motivos

            anomalias.append(
                {
                    "serial": ordem["serial"],
                    "modelo": ordem["modelo"],
                    "started_at": ordem["started_at"],
                    "finished_at": ordem["finished_at"],
                    "duracao_min": ordem["duracao_min"],
                    "motivos": motivos,
                }
            )

    return ordens, anomalias


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] _meses_periodo
# [RESPONSABILIDADE] Gerar labels mensais entre data inicial e final
# ====================================================================
def _meses_periodo(data_inicio: date, data_fim: date) -> List[str]:
    atual = date(data_inicio.year, data_inicio.month, 1)
    limite = date(data_fim.year, data_fim.month, 1)

    meses = []

    while atual <= limite:
        meses.append(atual.strftime("%Y-%m"))

        if atual.month == 12:
            atual = date(atual.year + 1, 1, 1)
        else:
            atual = date(atual.year, atual.month + 1, 1)

    return meses


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] _montar_volume_mensal
# [RESPONSABILIDADE] Consolidar volume mensal por modelo
# ====================================================================
def _montar_volume_mensal(
    ordens: List[Dict], data_inicio: date, data_fim: date
) -> Dict:
    meses = _meses_periodo(data_inicio, data_fim)
    matriz = {mes: {modelo: 0 for modelo in MODELOS_PADRAO} for mes in meses}

    for ordem in ordens:
        mes_ref = ordem["mes_ref"]

        if mes_ref in matriz:
            matriz[mes_ref][ordem["modelo"]] += 1

    rows = []

    for mes in meses:
        item = {"mes_ref": mes}
        total = 0

        for modelo in MODELOS_PADRAO:
            item[modelo] = matriz[mes][modelo]
            total += matriz[mes][modelo]

        item["total"] = total
        rows.append(item)

    datasets = [
        {
            "label": modelo,
            "data": [matriz[mes][modelo] for mes in meses],
        }
        for modelo in MODELOS_PADRAO
    ]

    return {
        "labels": meses,
        "rows": rows,
        "datasets": datasets,
    }


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] _montar_tempo_medio_mensal
# [RESPONSABILIDADE] Consolidar tempo médio mensal por modelo
# ====================================================================
def _montar_tempo_medio_mensal(
    ordens_validas: List[Dict],
    anomalias: List[Dict],
    data_inicio: date,
    data_fim: date,
) -> Dict:
    meses = _meses_periodo(data_inicio, data_fim)
    buckets = {mes: {modelo: [] for modelo in MODELOS_PADRAO} for mes in meses}

    for ordem in ordens_validas:
        mes_ref = ordem["mes_ref"]

        if mes_ref in buckets:
            buckets[mes_ref][ordem["modelo"]].append(ordem["duracao_min"])

    rows = []

    for mes in meses:
        item = {"mes_ref": mes}

        for modelo in MODELOS_PADRAO:
            valores = buckets[mes][modelo]
            item[modelo] = round(mean(valores), 2) if valores else None

        rows.append(item)

    datasets = [
        {
            "label": modelo,
            "data": [row[modelo] for row in rows],
        }
        for modelo in MODELOS_PADRAO
    ]

    return {
        "labels": meses,
        "rows": rows,
        "datasets": datasets,
        "anomalias": anomalias,
    }


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] _montar_alarmes_componentes
# [RESPONSABILIDADE] Consolidar histórico e Pareto de alarmes por falta de componente
# ====================================================================
def _montar_alarmes_componentes(data_inicio: date, data_fim: date) -> Dict:
    inspector = inspect(db.engine)

    if not inspector.has_table("gp_component_alarm"):
        return {
            "disponivel": False,
            "historico": [],
            "pareto": [],
            "mensagem": "Tabela gp_component_alarm ainda não criada.",
        }

    sql_historico = """
    SELECT
        occurred_at,
        resolved_at,
        bench_id,
        modelo,
        serial,
        component_code,
        COALESCE(component_desc, component_code) AS component_label,
        downtime_min,
        status
    FROM gp_component_alarm
    WHERE DATE(occurred_at) BETWEEN :data_inicio AND :data_fim
    ORDER BY occurred_at DESC
    LIMIT 500
    """

    sql_pareto = """
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

    params = {
        "data_inicio": data_inicio.isoformat(),
        "data_fim": data_fim.isoformat(),
    }

    historico = [
        dict(row)
        for row in db.session.execute(text(sql_historico), params).mappings().all()
    ]

    pareto_raw = [
        dict(row)
        for row in db.session.execute(text(sql_pareto), params).mappings().all()
    ]

    total_downtime = sum(float(row["downtime_min"] or 0) for row in pareto_raw) or 1
    acumulado = 0
    pareto = []

    for row in pareto_raw:
        downtime = float(row["downtime_min"] or 0)
        acumulado += downtime

        pareto.append(
            {
                "component_label": row["component_label"],
                "alarm_count": int(row["alarm_count"]),
                "downtime_min": downtime,
                "cum_pct": round((acumulado / total_downtime) * 100, 2),
            }
        )

    return {
        "disponivel": True,
        "historico": historico,
        "pareto": pareto,
    }


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] _buscar_dias_ativos
# [RESPONSABILIDADE] Listar dias com início ou fim de etapa registrado
# ====================================================================
def _buscar_dias_ativos(data_inicio: date, data_fim: date) -> set:
    dialeto = _dialeto_banco()

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

    registros = db.session.execute(
        text(sql),
        {
            "data_inicio": data_inicio.isoformat(),
            "data_fim": data_fim.isoformat(),
        },
    ).fetchall()

    return {str(row[0]) for row in registros}


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] _dias_uteis_periodo
# [RESPONSABILIDADE] Obter dias úteis pelo calendário oficial ou fallback segunda-sexta
# ====================================================================
def _dias_uteis_periodo(data_inicio: date, data_fim: date) -> List[date]:
    inspector = inspect(db.engine)

    if inspector.has_table("work_calendar"):
        sql = """
        SELECT dia
        FROM work_calendar
        WHERE dia BETWEEN :data_inicio AND :data_fim
          AND eh_dia_util = 1
        ORDER BY dia
        """

        registros = db.session.execute(
            text(sql),
            {
                "data_inicio": data_inicio.isoformat(),
                "data_fim": data_fim.isoformat(),
            },
        ).fetchall()

        return [datetime.strptime(str(row[0]), "%Y-%m-%d").date() for row in registros]

    dias = []
    atual = data_inicio

    while atual <= data_fim:
        if atual.weekday() < 5:
            dias.append(atual)

        atual += timedelta(days=1)

    return dias


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
# [NOME] _montar_ociosidade
# [RESPONSABILIDADE] Cruzar calendário de trabalho com dias de produção
# ====================================================================
def _montar_ociosidade(data_inicio: date, data_fim: date) -> Dict:
    dias_uteis = _dias_uteis_periodo(data_inicio, data_fim)
    dias_ativos = _buscar_dias_ativos(data_inicio, data_fim)

    dias_ociosos = [dia for dia in dias_uteis if dia.isoformat() not in dias_ativos]
    dias_produtivos = [dia for dia in dias_uteis if dia.isoformat() in dias_ativos]

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
# FUNÇÃO: parse_periodo_indicadores
# FUNÇÃO: build_producao_indicadores_payload
# FUNÇÃO: _dialeto_banco
# FUNÇÃO: _buscar_ordens_finalizadas
# FUNÇÃO: _quantil
# FUNÇÃO: _marcar_anomalias_tempo
# FUNÇÃO: _meses_periodo
# FUNÇÃO: _montar_volume_mensal
# FUNÇÃO: _montar_tempo_medio_mensal
# FUNÇÃO: _montar_alarmes_componentes
# FUNÇÃO: _buscar_dias_ativos
# FUNÇÃO: _dias_uteis_periodo
# FUNÇÃO: _weekday_ptbr
# FUNÇÃO: _montar_ociosidade
# ====================================================================
