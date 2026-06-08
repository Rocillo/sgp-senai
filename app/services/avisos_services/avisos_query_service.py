from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Tuple

from app.models_sqla import EstruturaMaquina, Peca
from app.services.montagem.capacidade_service import calcular_capacidade_modelo

# ====================================================================
# [BLOCO] BLOCO_UTIL
# [NOME] MODELOS_AVISOS
# [RESPONSABILIDADE] Mapear modelos monitorados para seus códigos de conjunto
# ====================================================================
MODELOS_AVISOS: List[Tuple[str, str]] = [
    ("PM2100", "7-000"),
    ("PM2200", "2-000"),
    ("PM700", "28-000"),
    ("PM25", "PM0025"),
]
# ====================================================================
# [FIM BLOCO] MODELOS_AVISOS
# ====================================================================


def _buscar_conjunto(codigo_conjunto: str) -> Peca | None:
    return Peca.query.filter_by(codigo_pneumark=codigo_conjunto).first()


def _listar_pecas_criticas(codigo_conjunto: str, estoque_maximo: int) -> List[Dict]:
    estrutura = EstruturaMaquina.query.filter_by(codigo_maquina=codigo_conjunto).all()

    codigos_pecas = [item.codigo_peca for item in estrutura]
    pecas_db = Peca.query.filter(Peca.codigo_pneumark.in_(codigos_pecas)).all()

    mapa_pecas = {p.codigo_pneumark: p for p in pecas_db}

    pecas: List[Dict] = []

    for item in estrutura:
        consumo = int(item.quantidade or 0)
        peca = mapa_pecas.get(item.codigo_peca)

        estoque_atual = int((peca.estoque_atual if peca else 0) or 0)
        necessario = consumo * estoque_maximo

        if consumo <= 0 or estoque_atual >= necessario:
            continue

        pecas.append(
            {
                "codigo": item.codigo_peca,
                "descricao": (peca.descricao if peca else "PEÇA NÃO ENCONTRADA")
                or "SEM DESCRIÇÃO",
                "estoque_atual": estoque_atual,
                "necessario_para_maximo": necessario,
                "quantidade_sugerida": None,
            }
        )

    pecas.sort(
        key=lambda x: (x["necessario_para_maximo"] - x["estoque_atual"]),
        reverse=True,
    )

    return pecas


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] listar_avisos_capacidade
# [RESPONSABILIDADE] Montar avisos ativos comparando capacidade produtiva com estoque máximo
# ====================================================================
def listar_avisos_capacidade() -> List[Dict]:
    avisos: List[Dict] = []
    agora = datetime.now()

    for modelo, codigo_conjunto in MODELOS_AVISOS:
        conjunto = _buscar_conjunto(codigo_conjunto)
        if not conjunto:
            continue

        estoque_maximo = int(conjunto.estoque_maximo or 0)
        if estoque_maximo <= 0:
            continue

        capacidade_info = calcular_capacidade_modelo(modelo)
        capacidade = int(capacidade_info.get("capacidade") or 0)

        if capacidade > estoque_maximo:
            continue

        pecas_criticas = _listar_pecas_criticas(codigo_conjunto, estoque_maximo)

        avisos.append(
            {
                "codigo": f"capacidade-{modelo.lower()}",
                "severidade": "critico",
                "titulo": f"Atenção: Capacidade produtiva da {modelo} abaixo do estoque máximo.",
                "descricao": "A montagem será comprometida.",
                "modelo": modelo,
                "origem": "Capacidade Produtiva",
                "data_aviso": agora,
                "lido_por": None,
                "lido_em": None,
                "status": "novo",
                "capacidade_atual": capacidade,
                "estoque_maximo": estoque_maximo,
                "pecas_criticas": pecas_criticas,
                "historico": [],
            }
        )

    return avisos


# ====================================================================
# [FIM BLOCO] listar_avisos_capacidade
# ====================================================================
