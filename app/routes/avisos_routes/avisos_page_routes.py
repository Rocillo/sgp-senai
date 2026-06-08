from flask import Blueprint, render_template
from flask_login import current_user, login_required

from app.services.avisos_services.avisos_action_service import marcar_aviso_como_lido
from app.services.avisos_services.avisos_service import montar_painel_avisos

# ====================================================================
# [BLOCO] BLUEPRINT
# [NOME] avisos_page_bp
# [RESPONSABILIDADE] Registrar rotas HTML da central de avisos
# ====================================================================
avisos_page_bp = Blueprint("avisos_page_bp", __name__, url_prefix="/producao/avisos")
# ====================================================================
# [FIM BLOCO] avisos_page_bp
# ====================================================================


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] home_avisos
# [RESPONSABILIDADE] Renderizar tela principal dos avisos da produção e registrar leitura dos avisos exibidos
# ====================================================================
@avisos_page_bp.route("/", methods=["GET"])
@login_required
def home_avisos():
    painel = montar_painel_avisos()

    for aviso in painel["avisos"]:
        codigo_aviso = aviso.get("codigo")
        if not codigo_aviso:
            continue

        marcar_aviso_como_lido(
            codigo_aviso=codigo_aviso,
            usuario_nome=current_user.username,
            usuario_id=getattr(current_user, "id", None),
        )

    painel = montar_painel_avisos()

    return render_template(
        "producao_templates/avisos_templates/home_avisos.html",
        avisos=painel["avisos"],
        avisos_qtd=painel["avisos_qtd"],
    )


# ====================================================================
# [FIM BLOCO] home_avisos
# ====================================================================
