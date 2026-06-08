from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.services.avisos_services.avisos_action_service import (
    comunicar_setor,
    marcar_aviso_como_lido,
)

# ====================================================================
# [BLOCO] BLUEPRINT
# [NOME] avisos_action_bp
# [RESPONSABILIDADE] Registrar rotas de ação da central de avisos
# ====================================================================
avisos_action_bp = Blueprint(
    "avisos_action_bp", __name__, url_prefix="/producao/avisos/action"
)
# ====================================================================
# [FIM BLOCO] avisos_action_bp
# ====================================================================


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] marcar_lido
# [RESPONSABILIDADE] Marcar aviso como lido e persistir usuário + timestamp
# ====================================================================
@avisos_action_bp.route("/<codigo_aviso>/ler", methods=["POST"])
@login_required
def marcar_lido(codigo_aviso):
    payload = marcar_aviso_como_lido(
        codigo_aviso=codigo_aviso,
        usuario_nome=current_user.username,
        usuario_id=getattr(current_user, "id", None),
    )
    return jsonify(payload), (200 if payload.get("ok") else 404)


# ====================================================================
# [FIM BLOCO] marcar_lido
# ====================================================================


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] comunicar
# [RESPONSABILIDADE] Comunicar setor e persistir evento operacional
# ====================================================================
@avisos_action_bp.route("/<codigo_aviso>/comunicar/<setor>", methods=["POST"])
@login_required
def comunicar(codigo_aviso, setor):
    payload = comunicar_setor(
        codigo_aviso=codigo_aviso,
        setor=setor,
        usuario_nome=current_user.username,
        usuario_id=getattr(current_user, "id", None),
    )
    return jsonify(payload), (200 if payload.get("ok") else 404)


# ====================================================================
# [FIM BLOCO] comunicar
# ====================================================================


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] resolver
# [RESPONSABILIDADE] Marcar aviso como resolvido (preparado para próxima etapa)
# ====================================================================
@avisos_action_bp.route("/<codigo_aviso>/resolver", methods=["POST"])
@login_required
def resolver(codigo_aviso):
    # placeholder para próxima fase (status resolvido)
    return (
        jsonify(
            {
                "ok": True,
                "codigo": codigo_aviso,
                "acao": "resolver",
                "usuario": current_user.username,
                "observacao": "Rota preparada - lógica será implementada na próxima etapa.",
            }
        ),
        200,
    )


# ====================================================================
# [FIM BLOCO] resolver
# ====================================================================
