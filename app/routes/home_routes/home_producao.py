# app/routes/home_routes/home_producao.py
from datetime import date
from flask_login import login_required
from flask import Blueprint, render_template, url_for, redirect, request

# ====================================================================
# [BLOCO] BLUEPRINT
# [NOME] home_producao_bp
# [RESPONSABILIDADE] Registrar rotas do módulo de produção com prefixo /producao
# ====================================================================
home_producao_bp = Blueprint("home_producao_bp", __name__, url_prefix="/producao")


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] home_producao
# [RESPONSABILIDADE] Renderizar página inicial do módulo de produção com cards de navegação
# ====================================================================
@home_producao_bp.route("/", methods=["GET"])
@login_required
def home_producao():
    cards = [
        {
            "title": "Montar Máquina",
            "desc": "Baixar estrutura completa do modelo.",
            "icon": "fa-cogs",
            "endpoint": url_for("maquinas_bp.pagina_montagem"),
            "badge": "Ativo",
        },
        {
            "title": "Gerenciar Produção",
            "desc": "Configurar bancadas, tempos e checklists por modelo.",
            "icon": "fa-clipboard-check",
            "endpoint": "/producao/gp/setup",
        },
        {
            "title": "Painel Visual",
            "desc": "Status em tempo real da produção.",
            "icon": "fa-chart-line",
            "endpoint": "/producao/gp/painel/",  # vai direto pro painel
        },
        {
            "title": "Indicadores",
            "desc": "KPIs e metas do setor.",
            "icon": "fa-gauge-high",
            "endpoint": url_for("home_producao_bp.placeholder", slug="indicadores"),
        },
        {
            "title": "Rastreabilidade das Máquinas",
            "desc": "Consultar histórico completo de produção.",
            "icon": "fa-history",
            "endpoint": url_for("gp_rastreabilidade_bp.rastreabilidade_senha"),
        },
        {
            "title": "Relatórios",
            "desc": "Consolidados por período e modelo.",
            "icon": "fa-file-alt",
            "endpoint": url_for("home_producao_bp.placeholder", slug="relatorios"),
        },
    ]

    try:
        breadcrumb_url = url_for("modulos_bp.tela_modulos")
    except Exception:
        breadcrumb_url = "/"

    return render_template(
        "home_templates/home_producao.html",
        cards=cards,
        breadcrumb_url=breadcrumb_url,
        avisos_qtd=3,
        avisos_href=url_for("avisos_page_bp.home_avisos"),
    )


# ====================================================================
# [FIM BLOCO] home_producao
# ====================================================================


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] home_avisos_legacy_redirect
# [RESPONSABILIDADE] Redirecionar rota legada da central de avisos para o blueprint oficial
# ====================================================================
@home_producao_bp.route("/avisos-legacy", methods=["GET"])
@login_required
def home_avisos_legacy_redirect():
    return redirect(url_for("avisos_page_bp.home_avisos"), code=302)


# ====================================================================
# [FIM BLOCO] home_avisos_legacy_redirect
# ====================================================================


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] placeholder
# [RESPONSABILIDADE] Redirecionar para endpoints existentes ou exibir mensagem de recurso indisponível
# ====================================================================
@home_producao_bp.route("/placeholder/<slug>", methods=["GET"])
@login_required
def placeholder(slug):

    # ====================================================================
    # [BLOCO] INDICADORES
    # [RESPONSABILIDADE] Renderizar tela gerencial de indicadores
    # ====================================================================
    if slug == "indicadores":
        hoje = date.today()

        data_inicio_param = request.args.get("data_inicio")
        data_fim_param = request.args.get("data_fim")

        data_inicio = data_inicio_param or hoje.replace(day=1).isoformat()
        data_fim = data_fim_param or hoje.isoformat()

        return render_template(
            "indicadores_templates/producao_indicadores.html",
            indicadores_api_url=url_for("indicadores_api_bp.api_indicadores_producao"),
            filtros_iniciais={
                "data_inicio": data_inicio,
                "data_fim": data_fim,
            },
        )
    # ====================================================================
    # [FIM BLOCO] INDICADORES
    # ====================================================================

    mapping = {
        "montar-maquina": ("maquinas_bp.pagina_montagem", {}),
        "painel-visual": (
            None,
            {"redirect": "/producao/gp/painel/"},
        ),
    }

    if slug in mapping:
        endpoint, params = mapping[slug]

        if endpoint:
            return redirect(url_for(endpoint, **params), code=302)

        if "redirect" in params:
            return redirect(params["redirect"], code=302)

    return render_template(
        "home_templates/home_producao.html",
        cards=[],
        placeholder=f'Recurso "{slug}" ainda não disponível.',
    )


# ====================================================================
# [FIM BLOCO] placeholder
# ====================================================================

# ====================================================================
# [FIM BLOCO] home_producao_bp
# ====================================================================

# ====================================================================
# MAPA DO ARQUIVO
# --------------------------------------------------------------------
# BLUEPRINT: home_producao_bp
# FUNÇÃO: home_producao
# FUNÇÃO: placeholder
# ====================================================================
