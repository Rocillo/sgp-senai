# app/services/estoque_service.py

import logging
from datetime import datetime
from sqlalchemy import func
from app.models_sqla import db, Peca

# ====================================================================
# [BLOCO] CONFIG_LOGGER
# [NOME] logger
# [RESPONSABILIDADE] Inicializar logger do módulo para rastreamento do serviço de estoque
# ====================================================================
logger = logging.getLogger(__name__)
# ====================================================================
# [FIM BLOCO] logger
# ====================================================================


# ====================================================================
# [BLOCO] BLOCO_DB
# [NOME] update_stock_after_finish
# [RESPONSABILIDADE] Wrapper de compatibilidade para concluir produto acabado usando a rotina oficial
# ====================================================================
def update_stock_after_finish(
    model_code: str,
    quantidade: int = 1,
    usuario: str = "Sistema",
    referencia: Optional[str] = None,
    session=None,
) -> str:
    """
    Wrapper de compatibilidade.

    IMPORTANTE:
    - Não faz mais busca direta de model_code em Peca.codigo_pneumark.
    - Não grava campos inexistentes como updated_at.
    - Delega a regra oficial para registrar_conclusao_produto_acabado().
    - Não faz commit aqui quando receber session externa.
    Retorna o codigo_pneumark do conjunto movimentado.
    """
    if not model_code or not str(model_code).strip():
        raise ValueError("model_code ausente para conclusão de produto acabado.")

    try:
        from app.routes.producao_routes.maquinas_routes.consumo_service import (
            registrar_conclusao_produto_acabado,
        )
    except Exception as e:
        logger.error(
            f"[Estoque] Falha ao importar registrar_conclusao_produto_acabado: {e}"
        )
        raise

    sess = session or db.session

    try:
        codigo_conjunto = registrar_conclusao_produto_acabado(
            modelo=str(model_code).strip(),
            quantidade=quantidade,
            usuario=(usuario or "Sistema"),
            referencia=referencia,
            session=sess,
        )

        logger.info(
            f"[Estoque] Conclusão redirecionada para rotina oficial | "
            f"modelo={model_code} conjunto={codigo_conjunto} quantidade={quantidade} referencia={referencia}"
        )

        return codigo_conjunto

    except Exception as e:
        logger.error(
            f"[Estoque] Erro ao concluir produto acabado para modelo={model_code}: {e}"
        )
        raise


# ====================================================================
# [FIM BLOCO] update_stock_after_finish
# ====================================================================

# ====================================================================
# MAPA DO ARQUIVO
# --------------------------------------------------------------------
# CONFIG_LOGGER: logger
# BLOCO_DB: update_stock_after_finish
# ====================================================================
