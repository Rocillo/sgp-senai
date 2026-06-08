from __future__ import annotations

from datetime import datetime
from typing import Dict

from app import db
from app.models.avisos_models.aviso import Aviso
from app.models.avisos_models.aviso_destinatario import AvisoDestinatario
from app.models.avisos_models.aviso_evento import AvisoEvento


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] _buscar_aviso_por_codigo
# [RESPONSABILIDADE] Localizar aviso persistido pelo código único
# ====================================================================
def _buscar_aviso_por_codigo(codigo_aviso: str) -> Aviso | None:
    return Aviso.query.filter_by(codigo=codigo_aviso).first()


# ====================================================================
# [FIM BLOCO] _buscar_aviso_por_codigo
# ====================================================================


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] marcar_aviso_como_lido
# [RESPONSABILIDADE] Persistir leitura do aviso e registrar evento operacional
# ====================================================================
def marcar_aviso_como_lido(
    codigo_aviso: str,
    usuario_nome: str,
    usuario_id: int | None = None,
) -> Dict:
    aviso = _buscar_aviso_por_codigo(codigo_aviso)
    if not aviso:
        return {
            "ok": False,
            "codigo": codigo_aviso,
            "acao": "lido",
            "erro": "aviso_nao_encontrado",
        }

    agora = datetime.now()

    if not aviso.lido_em:
        aviso.lido_por_user_id = usuario_id
        aviso.lido_por_nome = usuario_nome
        aviso.lido_em = agora

        evento = AvisoEvento(
            aviso_id=aviso.id,
            tipo_evento="lido",
            usuario_id=usuario_id,
            usuario_nome=usuario_nome,
            observacao="Aviso marcado como lido.",
            created_at=agora,
        )
        db.session.add(evento)
        db.session.commit()

    return {
        "ok": True,
        "codigo": codigo_aviso,
        "acao": "lido",
        "usuario": aviso.lido_por_nome,
        "quando": aviso.lido_em.strftime("%d/%m/%Y %H:%M") if aviso.lido_em else None,
        "persistido": True,
    }


# ====================================================================
# [FIM BLOCO] marcar_aviso_como_lido
# ====================================================================


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] comunicar_setor
# [RESPONSABILIDADE] Persistir comunicação do aviso para um setor, definir responsável da ocorrência e preparar link externo do WhatsApp Web
# ====================================================================
def comunicar_setor(
    codigo_aviso: str,
    setor: str,
    usuario_nome: str,
    usuario_id: int | None = None,
) -> Dict:
    from app.utils.whatsapp_utils import enviar_whatsapp_aviso_setor

    aviso = _buscar_aviso_por_codigo(codigo_aviso)
    if not aviso:
        return {
            "ok": False,
            "codigo": codigo_aviso,
            "acao": "comunicado",
            "erro": "aviso_nao_encontrado",
        }

    agora = datetime.now()
    setor_normalizado = (setor or "").strip().lower()

    destinatario = AvisoDestinatario.query.filter_by(
        aviso_id=aviso.id,
        setor=setor_normalizado,
    ).first()

    if not destinatario:
        destinatario = AvisoDestinatario(
            aviso_id=aviso.id,
            setor=setor_normalizado,
            status="comunicado",
            comunicado_por_user_id=usuario_id,
            comunicado_por_nome=usuario_nome,
            comunicado_em=agora,
        )
        db.session.add(destinatario)

    if not (aviso.departamento_responsavel or "").strip():
        aviso.departamento_responsavel = setor_normalizado

        evento_responsavel = AvisoEvento(
            aviso_id=aviso.id,
            tipo_evento="responsavel_definido",
            usuario_id=usuario_id,
            usuario_nome=usuario_nome,
            destino=setor_normalizado,
            observacao=f"responsável definido como {setor_normalizado}",
            created_at=agora,
        )
        db.session.add(evento_responsavel)

    evento = AvisoEvento(
        aviso_id=aviso.id,
        tipo_evento="comunicado",
        usuario_id=usuario_id,
        usuario_nome=usuario_nome,
        destino=setor_normalizado,
        observacao=f"Aviso comunicado ao setor {setor_normalizado}.",
        created_at=agora,
    )
    db.session.add(evento)

    if aviso.status == "novo":
        aviso.status = "em_tratamento"

    db.session.commit()

    whatsapp_payload = enviar_whatsapp_aviso_setor(
        ocorrencia_codigo=aviso.ocorrencia_codigo,
        codigo_aviso=codigo_aviso,
        titulo=aviso.titulo,
        descricao=aviso.descricao,
        modelo=aviso.modelo,
        capacidade_atual=aviso.capacidade_atual,
        estoque_maximo=aviso.estoque_maximo,
        setor=setor_normalizado,
        usuario_nome=usuario_nome,
    )

    return {
        "ok": True,
        "codigo": codigo_aviso,
        "ocorrencia_codigo": aviso.ocorrencia_codigo,
        "acao": "comunicado",
        "setor": setor_normalizado,
        "usuario": usuario_nome,
        "quando": agora.strftime("%d/%m/%Y %H:%M"),
        "persistido": True,
        "departamento_responsavel": aviso.departamento_responsavel,
        "whatsapp_ativo": whatsapp_payload.get("whatsapp_ativo"),
        "whatsapp_simulado": whatsapp_payload.get("whatsapp_simulado"),
        "destino_whatsapp_setor": whatsapp_payload.get("destino_setor"),
        "destino_whatsapp_grupo": whatsapp_payload.get("grupo_destino"),
        "envio_whatsapp_status": whatsapp_payload.get("status_envio"),
        "whatsapp_web_url": whatsapp_payload.get("whatsapp_web_url"),
    }


# ====================================================================
# [FIM BLOCO] comunicar_setor
# ====================================================================
