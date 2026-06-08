"""Testes simples do módulo de Indicadores usando unittest."""

import unittest
from datetime import date
from app import create_app, db


class TestIndicadoresAPI(unittest.TestCase):
    """Testes da API de Indicadores."""

    def setUp(self):
        """Configura ambiente de teste."""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        """Limpa ambiente de teste."""
        self.app_context.pop()

    def test_parse_periodo_indicadores_valido(self):
        """Testa parsing de período com datas válidas."""
        from app.services.indicadores_services.indicadores_service import (
            parse_periodo_indicadores,
        )

        args = {"data_inicio": "2026-05-01", "data_fim": "2026-05-31"}
        data_inicio, data_fim = parse_periodo_indicadores(args)

        self.assertEqual(data_inicio, date(2026, 5, 1))
        self.assertEqual(data_fim, date(2026, 5, 31))

    def test_parse_periodo_indicadores_sem_datas(self):
        """Testa parsing sem datas (usa mês atual)."""
        from app.services.indicadores_services.indicadores_service import (
            parse_periodo_indicadores,
        )

        args = {}
        data_inicio, data_fim = parse_periodo_indicadores(args)

        self.assertEqual(data_inicio.day, 1)
        self.assertGreaterEqual(data_fim, data_inicio)

    def test_parse_periodo_indicadores_formato_invalido(self):
        """Testa parsing com formato inválido."""
        from app.services.indicadores_services.indicadores_service import (
            parse_periodo_indicadores,
        )

        args = {"data_inicio": "01/05/2026", "data_fim": "31/05/2026"}

        with self.assertRaises(ValueError) as context:
            parse_periodo_indicadores(args)

        self.assertIn("YYYY-MM-DD", str(context.exception))

    def test_parse_periodo_indicadores_data_inicio_maior(self):
        """Testa parsing com data_inicio > data_fim."""
        from app.services.indicadores_services.indicadores_service import (
            parse_periodo_indicadores,
        )

        args = {"data_inicio": "2026-05-31", "data_fim": "2026-05-01"}

        with self.assertRaises(ValueError) as context:
            parse_periodo_indicadores(args)

        self.assertIn("maior", str(context.exception))

    def test_build_producao_indicadores_payload(self):
        """Testa construção do payload de indicadores."""
        from app.services.indicadores_services.indicadores_service import (
            build_producao_indicadores_payload,
        )

        payload = build_producao_indicadores_payload(
            data_inicio=date(2026, 5, 1), data_fim=date(2026, 5, 31)
        )

        self.assertTrue(payload["ok"])
        self.assertIn("periodo", payload)
        self.assertIn("modelos", payload)
        self.assertIn("resumo", payload)
        self.assertIn("volume", payload)
        self.assertIn("tempo_medio", payload)
        self.assertIn("alarmes_componentes", payload)
        self.assertIn("ociosidade", payload)

        # Verifica estrutura do resumo
        resumo = payload["resumo"]
        self.assertIn("maquinas_finalizadas", resumo)
        self.assertIn("tempo_medio_limpo_min", resumo)
        self.assertIn("anomalias_processo", resumo)
        self.assertIn("dias_produtivos", resumo)
        self.assertIn("dias_ociosos", resumo)
        self.assertIn("taxa_ociosidade_pct", resumo)

    def test_modelos_indicadores_existem(self):
        """Testa que modelos de indicadores existem."""
        from app.models_sqla import GPProductionAlarm, GPWorkingCalendar

        # Verifica que modelos podem ser instanciados
        alarm = GPProductionAlarm()
        calendar = GPWorkingCalendar()

        self.assertIsNotNone(alarm)
        self.assertIsNotNone(calendar)

    def test_tabelas_existem(self):
        """Testa que tabelas de indicadores existem."""
        from sqlalchemy import inspect

        inspector = inspect(db.engine)
        tables = inspector.get_table_names()

        self.assertIn("gp_component_alarm", tables)
        self.assertIn("work_calendar", tables)

    def test_modelos_padrao(self):
        """Testa que modelos padrão estão definidos."""
        from app.services.indicadores_services.indicadores_service import MODELOS_PADRAO

        self.assertEqual(MODELOS_PADRAO, ["PM2100", "PM2200", "PM700"])

    def test_limite_duracao_processo(self):
        """Testa que limite de duração está definido."""
        from app.services.indicadores_services.indicadores_service import (
            LIMITE_DURACAO_PROCESSO_MIN,
        )

        self.assertEqual(LIMITE_DURACAO_PROCESSO_MIN, 16 * 60)


if __name__ == "__main__":
    unittest.main()
