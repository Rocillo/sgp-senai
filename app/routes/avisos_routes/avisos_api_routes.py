from flask import Blueprint, jsonify
from flask_login import login_required

from app.services.avisos_services.avisos_service import montar_painel_avisos

# ====================================================================
# [BLOCO] BLUEPRINT
# [NOME] avisos_api_bp
# [RESPONSABILIDADE] Registrar APIs JSON da central de avisos
# ====================================================================
avisos_api_bp = Blueprint("avisos_api_bp", __name__, url_prefix="/producao/avisos/api")
# ====================================================================
# [FIM BLOCO] avisos_api_bp
# ====================================================================


@avisos_api_bp.route("/lista", methods=["GET"])
@login_required
def api_lista_avisos():
    painel = montar_painel_avisos()
    return jsonify(painel), 200


@avisos_api_bp.route("/contador", methods=["GET"])
@login_required
def api_contador_avisos():
    painel = montar_painel_avisos()
    return jsonify({"avisos_qtd": painel["avisos_qtd"]}), 200
