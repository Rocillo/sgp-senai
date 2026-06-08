# ====================================================================
# [BLOCO] MÓDULO
# [NOME] indicadores_routes
# [RESPONSABILIDADE] Rotas API-First dos indicadores gerenciais de produção
# ====================================================================

from flask import Blueprint, jsonify, request
from flask_login import login_required

from app.services.indicadores_services.indicadores_service import (
    build_producao_indicadores_payload,
    parse_periodo_indicadores,
)

# ====================================================================
# [BLOCO] BLUEPRINT
# [NOME] indicadores_api_bp
# [RESPONSABILIDADE] Expor endpoints JSON para dashboards de indicadores
# ====================================================================
indicadores_api_bp = Blueprint(
    "indicadores_api_bp",
    __name__,
    url_prefix="/api/v1/indicadores",
)


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] api_indicadores_producao
# [RESPONSABILIDADE] Entregar payload consolidado dos indicadores gerenciais de produção
# ====================================================================
@indicadores_api_bp.route("/producao", methods=["GET"])
@login_required
def api_indicadores_producao():
    try:
        data_inicio, data_fim = parse_periodo_indicadores(request.args)

        payload = build_producao_indicadores_payload(
            data_inicio=data_inicio,
            data_fim=data_fim,
        )

        response = jsonify(payload)
        response.headers["Cache-Control"] = "no-store"
        return response, 200

    except ValueError as e:
        return (
            jsonify(
                {
                    "ok": False,
                    "erro": "parametros_invalidos",
                    "mensagem": str(e),
                }
            ),
            400,
        )

    except Exception as e:
        return (
            jsonify(
                {
                    "ok": False,
                    "erro": "falha_ao_processar_indicadores_producao",
                    "mensagem": str(e),
                }
            ),
            500,
        )


# ====================================================================
# [FIM BLOCO] api_indicadores_producao
# ====================================================================


# ====================================================================
# MAPA DO ARQUIVO
# --------------------------------------------------------------------
# BLUEPRINT: indicadores_api_bp
# FUNÇÃO: api_indicadores_producao
# ====================================================================
