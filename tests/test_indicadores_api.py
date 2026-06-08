"""Testes da API de Indicadores de Produção."""

import pytest
from datetime import date
from app import create_app, db


@pytest.fixture
def app():
    """Cria aplicação Flask para testes."""
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Cria cliente de teste."""
    return app.test_client()


def test_api_indicadores_producao_sem_autenticacao(client):
    """Testa que API requer autenticação."""
    response = client.get("/api/v1/indicadores/producao")
    assert response.status_code == 401 or response.status_code == 302


def test_parse_periodo_indicadores():
    """Testa parsing de período."""
    from app.services.indicadores_services.indicadores_service import (
        parse_periodo_indicadores,
    )

    # Teste com datas válidas
    args = {"data_inicio": "2026-05-01", "data_fim": "2026-05-31"}
    data_inicio, data_fim = parse_periodo_indicadores(args)

    assert data_inicio == date(2026, 5, 1)
    assert data_fim == date(2026, 5, 31)


def test_parse_periodo_indicadores_sem_datas():
    """Testa parsing sem datas (usa mês atual)."""
    from app.services.indicadores_services.indicadores_service import (
        parse_periodo_indicadores,
    )

    args = {}
    data_inicio, data_fim = parse_periodo_indicadores(args)

    assert data_inicio.day == 1
    assert data_fim >= data_inicio


def test_parse_periodo_indicadores_formato_invalido():
    """Testa parsing com formato inválido."""
    from app.services.indicadores_services.indicadores_service import (
        parse_periodo_indicadores,
    )

    args = {"data_inicio": "01/05/2026", "data_fim": "31/05/2026"}

    with pytest.raises(ValueError, match="Use o formato YYYY-MM-DD"):
        parse_periodo_indicadores(args)


def test_parse_periodo_indicadores_data_inicio_maior():
    """Testa parsing com data_inicio > data_fim."""
    from app.services.indicadores_services.indicadores_service import (
        parse_periodo_indicadores,
    )

    args = {"data_inicio": "2026-05-31", "data_fim": "2026-05-01"}

    with pytest.raises(ValueError, match="data_inicio não pode ser maior"):
        parse_periodo_indicadores(args)


def test_build_producao_indicadores_payload(app):
    """Testa construção do payload de indicadores."""
    from app.services.indicadores_services.indicadores_service import (
        build_producao_indicadores_payload,
    )

    with app.app_context():
        payload = build_producao_indicadores_payload(
            data_inicio=date(2026, 5, 1), data_fim=date(2026, 5, 31)
        )

        assert payload["ok"] is True
        assert "periodo" in payload
        assert "modelos" in payload
        assert "resumo" in payload
        assert "volume" in payload
        assert "tempo_medio" in payload
        assert "alarmes_componentes" in payload
        assert "ociosidade" in payload

        # Verifica estrutura do resumo
        resumo = payload["resumo"]
        assert "maquinas_finalizadas" in resumo
        assert "tempo_medio_limpo_min" in resumo
        assert "anomalias_processo" in resumo
        assert "dias_produtivos" in resumo
        assert "dias_ociosos" in resumo
        assert "taxa_ociosidade_pct" in resumo


def test_modelos_indicadores_existem(app):
    """Testa que modelos de indicadores existem."""
    from app.models_sqla import GPProductionAlarm, GPWorkingCalendar

    with app.app_context():
        # Verifica que modelos podem ser instanciados
        alarm = GPProductionAlarm()
        calendar = GPWorkingCalendar()

        assert alarm is not None
        assert calendar is not None


def test_tabela_alarmes_existe(app):
    """Testa que tabela de alarmes existe."""
    from sqlalchemy import inspect

    with app.app_context():
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()

        assert "gp_component_alarm" in tables


def test_tabela_calendario_existe(app):
    """Testa que tabela de calendário existe."""
    from sqlalchemy import inspect

    with app.app_context():
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()

        assert "work_calendar" in tables
