# ====================================================================
# [BLOCO] MÓDULO
# [NOME] indicadores_routes
# [RESPONSABILIDADE] Expor blueprints do módulo de indicadores
# ====================================================================

from .indicadores_routes import indicadores_api_bp


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] init_app
# [RESPONSABILIDADE] Registrar blueprints do módulo quando utilizado no padrão init_app
# ====================================================================
def init_app(app):
    app.register_blueprint(indicadores_api_bp)


# ====================================================================
# [FIM BLOCO] init_app
# ====================================================================


__all__ = [
    "indicadores_api_bp",
    "init_app",
]
