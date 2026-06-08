from __future__ import annotations

# ====================================================================
# [BLOCO] CONFIG_OPERACIONAL
# [NOME] WHATSAPP_CLOUD_API_REFERENCIA
# [RESPONSABILIDADE] Centralizar referências operacionais da integração oficial do WhatsApp para manutenção futura
#
# DADOS IMPORTANTES DO AMBIENTE DE TESTE
# --------------------------------------------------------------------
# Número de teste exibido pela Meta:
# +1 555 657 2803
#
# Número de destino de teste atualmente autorizado:
# 5511944768124
#
# Phone Number ID:
# 963406960198641
#
# WhatsApp Business Account ID:
# 2191182971713688
#
# Versão atual da API utilizada:
# v25.0
#
# Token de acesso atual:
# [REMOVIDO DO CÓDIGO OPERACIONAL — usar somente em ambiente seguro]
#
# OBSERVAÇÕES IMPORTANTES
# --------------------------------------------------------------------
# 1) O grupo de WhatsApp ainda NÃO está implementado neste fluxo.
# 2) O envio atual está preparado para disparo 1:1 por setor.
# 3) O envio em produção atual está por WhatsApp Web com mensagem pronta.
# ====================================================================

from typing import Dict


# ====================================================================
# [BLOCO] BLOCO_UTIL
# [NOME] WHATSAPP_AVISOS_CONFIG
# [RESPONSABILIDADE] Centralizar números de destino e parâmetros operacionais dos avisos
# ====================================================================
WHATSAPP_AVISOS_ATIVO = True

WHATSAPP_API_VERSION = "v25.0"
WHATSAPP_PHONE_NUMBER_ID = "963406960198641"
WHATSAPP_ACCESS_TOKEN = None

WHATSAPP_NUMERO_GRUPO_AVISOS = None

WHATSAPP_NUMEROS_POR_SETOR = {
    "compras": "5511944768124",
    "qualidade": "5511943364000",
    "projetos": "5511943364000",
}
# ====================================================================
# [FIM BLOCO] WHATSAPP_AVISOS_CONFIG
# ====================================================================


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] obter_destino_whatsapp_setor
# [RESPONSABILIDADE] Resolver o número WhatsApp configurado para o setor informado
# ====================================================================
def obter_destino_whatsapp_setor(setor: str) -> str | None:
    setor_normalizado = (setor or "").strip().lower()
    return WHATSAPP_NUMEROS_POR_SETOR.get(setor_normalizado)


# ====================================================================
# [FIM BLOCO] obter_destino_whatsapp_setor
# ====================================================================


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] montar_mensagem_whatsapp_aviso
# [RESPONSABILIDADE] Montar mensagem operacional de WhatsApp com contexto útil para ação do setor
# ====================================================================
def montar_mensagem_whatsapp_aviso(
    *,
    ocorrencia_codigo: str | None,
    codigo_aviso: str,
    titulo: str | None,
    descricao: str | None,
    modelo: str | None,
    capacidade_atual: int | None,
    estoque_maximo: int | None,
    setor: str,
    usuario_nome: str,
) -> str:
    setor_normalizado = (setor or "").strip().lower()
    titulo = (titulo or "").strip()
    descricao = (descricao or "").strip()
    modelo = (modelo or "").strip()

    quantidade_minima = None
    if capacidade_atual is not None and estoque_maximo is not None:
        quantidade_minima = max(estoque_maximo - capacidade_atual, 0)

    cabecalho = "🚨 *SGP | AVISO DE PRODUÇÃO*"
    ocorrencia = f"📌 *Ocorrência:* {ocorrencia_codigo or 'PENDENTE'}"
    setor_linha = f"🏭 *Setor acionado:* {setor_normalizado.upper()}"
    responsavel = f"👤 *Ação registrada por:* {usuario_nome}"

    if setor_normalizado == "compras":
        return (
            f"{cabecalho}\n\n"
            f"{ocorrencia}\n"
            f"{setor_linha}\n\n"
            f"⚠️ *Atenção:* a produção identificou necessidade de reposição.\n\n"
            f"🔩 *Item / modelo:* {modelo or codigo_aviso}\n"
            f"📝 *Título:* {titulo or 'Aviso operacional'}\n"
            f"📉 *Estoque atual:* {capacidade_atual if capacidade_atual is not None else '-'}\n"
            f"📦 *Estoque máximo desejado:* {estoque_maximo if estoque_maximo is not None else '-'}\n"
            f"🛒 *Quantidade mínima sugerida para compra:* {quantidade_minima if quantidade_minima is not None else '-'}\n\n"
            f"📄 *Resumo:* {descricao or 'Sem descrição adicional.'}\n\n"
            f"➡️ *Ação esperada:* avaliar compra / reposição para não comprometer a produção.\n"
            f"{responsavel}"
        )

    if setor_normalizado == "qualidade":
        return (
            f"{cabecalho}\n\n"
            f"{ocorrencia}\n"
            f"{setor_linha}\n\n"
            f"⚠️ *Atenção:* a produção registrou uma ocorrência que exige avaliação.\n\n"
            f"🔩 *Item / modelo:* {modelo or codigo_aviso}\n"
            f"📝 *Título:* {titulo or 'Aviso operacional'}\n"
            f"📄 *Resumo:* {descricao or 'Sem descrição adicional.'}\n\n"
            f"➡️ *Ação esperada:* verificar impacto e orientar tratativa.\n"
            f"{responsavel}"
        )

    return (
        f"{cabecalho}\n\n"
        f"{ocorrencia}\n"
        f"{setor_linha}\n\n"
        f"🔩 *Item / modelo:* {modelo or codigo_aviso}\n"
        f"📝 *Título:* {titulo or 'Aviso operacional'}\n"
        f"📄 *Resumo:* {descricao or 'Sem descrição adicional.'}\n\n"
        f"➡️ *Ação esperada:* verificar esta ocorrência e seguir tratativa.\n"
        f"{responsavel}"
    )


# ====================================================================
# [FIM BLOCO] montar_mensagem_whatsapp_aviso
# ====================================================================


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] enviar_whatsapp_aviso_setor
# [RESPONSABILIDADE] Preparar link do WhatsApp Web para envio manual assistido ao setor configurado
# ====================================================================
def enviar_whatsapp_aviso_setor(
    *,
    ocorrencia_codigo: str | None,
    codigo_aviso: str,
    titulo: str | None,
    descricao: str | None,
    modelo: str | None,
    capacidade_atual: int | None,
    estoque_maximo: int | None,
    setor: str,
    usuario_nome: str,
) -> Dict:
    from urllib.parse import quote

    destino_setor = obter_destino_whatsapp_setor(setor)
    mensagem = montar_mensagem_whatsapp_aviso(
        ocorrencia_codigo=ocorrencia_codigo,
        codigo_aviso=codigo_aviso,
        titulo=titulo,
        descricao=descricao,
        modelo=modelo,
        capacidade_atual=capacidade_atual,
        estoque_maximo=estoque_maximo,
        setor=setor,
        usuario_nome=usuario_nome,
    )

    if not destino_setor:
        return {
            "whatsapp_ativo": True,
            "whatsapp_simulado": False,
            "grupo_destino": WHATSAPP_NUMERO_GRUPO_AVISOS,
            "destino_setor": None,
            "mensagem": mensagem,
            "status_envio": "setor_sem_numero_configurado",
            "whatsapp_web_url": None,
        }

    whatsapp_web_url = f"https://wa.me/{destino_setor}?text={quote(mensagem)}"

    return {
        "whatsapp_ativo": True,
        "whatsapp_simulado": False,
        "grupo_destino": WHATSAPP_NUMERO_GRUPO_AVISOS,
        "destino_setor": destino_setor,
        "mensagem": mensagem,
        "status_envio": "link_whatsapp_web_pronto",
        "whatsapp_web_url": whatsapp_web_url,
    }


# ====================================================================
# [FIM BLOCO] enviar_whatsapp_aviso_setor
# ====================================================================
