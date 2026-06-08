"""Teste final completo do módulo de indicadores."""

from datetime import date
from app import create_app

app = create_app()

print("=" * 70)
print("TESTE FINAL: Módulo de Indicadores de Produção")
print("=" * 70)

with app.app_context():
    # Teste 1: Verificar imports
    print("\n[1] Verificando imports dos modelos...")
    try:
        from app.models_sqla import GPProductionAlarm, GPWorkingCalendar

        print("   OK: Modelos importados com sucesso")
    except Exception as e:
        print(f"   ERRO: {e}")

    # Teste 2: Verificar tabelas no banco
    print("\n[2] Verificando tabelas no banco de dados...")
    try:
        from sqlalchemy import inspect
        from app import db

        inspector = inspect(db.engine)
        tables = inspector.get_table_names()

        if "gp_component_alarm" in tables:
            print("   OK: Tabela gp_component_alarm existe")
        else:
            print("   ERRO: Tabela gp_component_alarm NAO encontrada")

        if "work_calendar" in tables:
            print("   OK: Tabela work_calendar existe")
        else:
            print("   ERRO: Tabela work_calendar NAO encontrada")
    except Exception as e:
        print(f"   ERRO: {e}")

    # Teste 3: Verificar services
    print("\n[3] Verificando services...")
    try:
        from app.services.indicadores_services.indicadores_service import (
            build_producao_indicadores_payload,
            parse_periodo_indicadores,
        )
        from app.services.indicadores_services.alarmes_service import (
            registrar_alarmes_falta_componentes,
            reconciliar_alarmes_abertos_por_componente,
        )
        from app.services.indicadores_services.calendario_service import (
            obter_dias_uteis_operacionais,
            montar_indicador_ociosidade,
        )

        print("   OK: Todos os services importados com sucesso")
    except Exception as e:
        print(f"   ERRO: {e}")

    # Teste 4: Verificar blueprint e rotas
    print("\n[4] Verificando blueprint e rotas...")
    try:
        rotas_indicadores = [
            rule.rule for rule in app.url_map.iter_rules() if "indicadores" in rule.rule
        ]
        if rotas_indicadores:
            print(f"   OK: {len(rotas_indicadores)} rota(s) registrada(s):")
            for rota in rotas_indicadores:
                print(f"      - {rota}")
        else:
            print("   ERRO: Nenhuma rota de indicadores encontrada")
    except Exception as e:
        print(f"   ERRO: {e}")

    # Teste 5: Testar API
    print("\n[5] Testando API de indicadores...")
    try:
        from app.services.indicadores_services.indicadores_service import (
            build_producao_indicadores_payload,
        )

        payload = build_producao_indicadores_payload(
            data_inicio=date(2026, 5, 1),
            data_fim=date(2026, 5, 22),
        )

        print(f"   OK: API retornou payload com {len(payload)} chaves")
        print(f"      - ok: {payload.get('ok')}")
        print(f"      - periodo: {payload.get('periodo')}")
        print(f"      - modelos: {payload.get('modelos')}")
        print(
            f"      - resumo.maquinas_finalizadas: {payload.get('resumo', {}).get('maquinas_finalizadas')}"
        )
        print(
            f"      - alarmes_componentes.disponivel: {payload.get('alarmes_componentes', {}).get('disponivel')}"
        )
    except Exception as e:
        print(f"   ERRO: {e}")
        import traceback

        traceback.print_exc()

    # Teste 6: Verificar template
    print("\n[6] Verificando template...")
    try:
        import os

        template_path = os.path.join(
            app.root_path,
            "templates",
            "indicadores_templates",
            "producao_indicadores.html",
        )
        if os.path.exists(template_path):
            print(f"   OK: Template encontrado em {template_path}")
        else:
            print(f"   ERRO: Template NAO encontrado")
    except Exception as e:
        print(f"   ERRO: {e}")

    # Teste 7: Verificar JavaScript
    print("\n[7] Verificando JavaScript...")
    try:
        import os

        js_path = os.path.join(
            app.root_path, "static", "js", "indicadores", "producao_indicadores.js"
        )
        if os.path.exists(js_path):
            print(f"   OK: JavaScript encontrado em {js_path}")
        else:
            print(f"   ERRO: JavaScript NAO encontrado")
    except Exception as e:
        print(f"   ERRO: {e}")

print("\n" + "=" * 70)
print("TESTE FINAL CONCLUIDO")
print("=" * 70)
