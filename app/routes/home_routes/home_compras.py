from flask import Blueprint, render_template
from flask_login import login_required

# ====================================================================
# [BLOCO] BLUEPRINT
# [NOME] compras_bp
# [RESPONSABILIDADE] Registrar rotas principais do módulo de compras
# ====================================================================
compras_bp = Blueprint("compras_bp", __name__)


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] tela_compras
# [RESPONSABILIDADE] Renderizar tela principal de compras com autenticação obrigatória
# ====================================================================
@compras_bp.route("/compras")
@login_required
def tela_compras():
    return render_template("home_templates/home_compras.html")


# ====================================================================
# [FIM BLOCO] tela_compras
# ====================================================================


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] requisicao_de_compras
# [RESPONSABILIDADE] Redirecionar para a listagem de requisições de compras
# ====================================================================
@compras_bp.route("/compras/requisicoes-atalho")
@login_required
def requisicao_de_compras():
    return render_template("compras_templates/requisicao_de_compras.html")


# ====================================================================
# [FIM BLOCO] requisicao_de_compras
# ====================================================================


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] manual_do_fornecedor
# [RESPONSABILIDADE] Renderizar tela do manual do fornecedor
# ====================================================================
@compras_bp.route("/compras/manual-fornecedor")
@login_required
def manual_do_fornecedor():
    return render_template("compras_templates/manual_do_fornecedor.html")


# ====================================================================
# [FIM BLOCO] manual_do_fornecedor
# ====================================================================


# ====================================================================
# [FIM BLOCO] compras_bp
# ====================================================================

# ====================================================================
# MAPA DO ARQUIVO
# --------------------------------------------------------------------
# BLUEPRINT: compras_bp
# FUNÇÃO: tela_compras
# FUNÇÃO: requisicao_de_compras
# FUNÇÃO: manual_do_fornecedor
# ====================================================================
