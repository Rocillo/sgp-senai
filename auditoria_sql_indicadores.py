"""Auditoria SQL - Validar queries dos indicadores."""

from datetime import date, datetime
from app import create_app, db
from sqlalchemy import text

app = create_app()

print("=" * 70)
print("AUDITORIA SQL: Queries dos Indicadores")
print("=" * 70)

with app.app_context():

    # Teste 1: Query de ordens finalizadas (SQLite)
    print("\n[1] Testando query _buscar_ordens_finalizadas (SQLite)...")
    try:
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
        LIMIT 5
        """

        result = db.session.execute(
            text(sql),
            {
                "data_inicio": "2026-01-01",
                "data_fim": "2026-12-31",
            },
        ).fetchall()

        print(f"   OK: Query retornou {len(result)} registro(s)")
        for row in result:
            print(f"      - ordem_id={row[0]}, modelo={row[2]}, duracao_min={row[5]}")

    except Exception as e:
        print(f"   ERRO: {e}")
        import traceback

        traceback.print_exc()

    # Teste 2: Query de dias ativos (SQLite)
    print("\n[2] Testando query _buscar_dias_ativos (SQLite)...")
    try:
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
        LIMIT 10
        """

        result = db.session.execute(
            text(sql),
            {
                "data_inicio": "2026-01-01",
                "data_fim": "2026-12-31",
            },
        ).fetchall()

        print(f"   OK: Query retornou {len(result)} dia(s) ativo(s)")
        for row in result[:5]:
            print(f"      - {row[0]}")

    except Exception as e:
        print(f"   ERRO: {e}")
        import traceback

        traceback.print_exc()

    # Teste 3: Query de alarmes
    print("\n[3] Testando query de alarmes...")
    try:
        sql = """
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
        LIMIT 5
        """

        result = db.session.execute(
            text(sql),
            {
                "data_inicio": "2026-01-01",
                "data_fim": "2026-12-31",
            },
        ).fetchall()

        print(f"   OK: Query retornou {len(result)} alarme(s)")
        for row in result:
            print(f"      - modelo={row[3]}, component={row[6]}, status={row[8]}")

    except Exception as e:
        print(f"   ERRO: {e}")
        import traceback

        traceback.print_exc()

    # Teste 4: Verificar ordens com finished_at NULL
    print("\n[4] Verificando ordens SEM finished_at...")
    try:
        sql = """
        SELECT COUNT(*) as cnt
        FROM gp_work_order
        WHERE finished_at IS NULL
        """

        result = db.session.execute(text(sql)).fetchone()
        print(f"   INFO: {result[0]} ordem(ns) sem finished_at")

        if result[0] > 0:
            print("   ALERTA: Ordens abertas não serão contabilizadas nos indicadores")

    except Exception as e:
        print(f"   ERRO: {e}")

    # Teste 5: Verificar stages com started_at NULL
    print("\n[5] Verificando stages SEM started_at...")
    try:
        sql = """
        SELECT COUNT(*) as cnt
        FROM gp_work_stage
        WHERE started_at IS NULL
        """

        result = db.session.execute(text(sql)).fetchone()
        print(f"   INFO: {result[0]} stage(s) sem started_at")

    except Exception as e:
        print(f"   ERRO: {e}")

    # Teste 6: Verificar durações negativas ou zero
    print("\n[6] Verificando durações inválidas...")
    try:
        sql = """
        WITH order_times AS (
            SELECT
                o.id AS ordem_id,
                o.serial,
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
            GROUP BY o.id, o.serial, o.finished_at
            HAVING MIN(s.started_at) IS NOT NULL
               AND COALESCE(o.finished_at, MAX(s.finished_at)) IS NOT NULL
        )
        SELECT COUNT(*) as cnt
        FROM order_times
        WHERE duracao_min <= 0
        """

        result = db.session.execute(text(sql)).fetchone()
        print(f"   INFO: {result[0]} ordem(ns) com duração <= 0")

        if result[0] > 0:
            print("   ALERTA: Durações inválidas serão marcadas como anomalias")

    except Exception as e:
        print(f"   ERRO: {e}")

    # Teste 7: Verificar work_calendar vazio
    print("\n[7] Verificando work_calendar...")
    try:
        sql = "SELECT COUNT(*) as cnt FROM work_calendar"
        result = db.session.execute(text(sql)).fetchone()
        print(f"   INFO: {result[0]} dia(s) cadastrado(s) no calendário")

        if result[0] == 0:
            print("   ALERTA: Calendário vazio - será usado fallback segunda-sexta")

    except Exception as e:
        print(f"   ERRO: {e}")

print("\n" + "=" * 70)
print("AUDITORIA SQL CONCLUÍDA")
print("=" * 70)
