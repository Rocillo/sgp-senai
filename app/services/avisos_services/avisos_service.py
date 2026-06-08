from __future__ import annotations

import re
from typing import Dict, List

from app import db
from app.models.avisos_models.aviso import Aviso
from app.models.avisos_models.aviso_evento import AvisoEvento
from .avisos_query_service import listar_avisos_capacidade


# ====================================================================
# [BLOCO] BLOCO_UTIL
# [NOME] _rotulo_tipo_aviso
# [RESPONSABILIDADE] Traduzir o tipo técnico do aviso para rótulo operacional
# ====================================================================
def _rotulo_tipo_aviso(tipo: str | None) -> str:
    mapa = {
        "capacidade": "Capacidade Produtiva",
        "qualidade": "Controle de Qualidade",
        "estoque": "Estoque",
        "processo": "Processo",
        "manutencao": "Manutenção",
    }
    return mapa.get((tipo or "").strip().lower(), "Ocorrência")


# ====================================================================
# [FIM BLOCO] _rotulo_tipo_aviso
# ====================================================================


# ====================================================================
# [BLOCO] BLOCO_UTIL
# [NOME] _normalizar_origem_aviso
# [RESPONSABILIDADE] Ajustar a origem exibida da ocorrência para padrão operacional
# ====================================================================
def _normalizar_origem_aviso(origem: str | None, tipo: str | None) -> str:
    origem_limpa = (origem or "").strip()

    if origem_limpa:
        if (tipo or "").strip().lower() == "capacidade" and origem_limpa.lower() in {
            "capacidade produtiva",
            "capacidade",
        }:
            return "Monitoramento Automático"
        return origem_limpa

    return "Monitoramento Automático"


# ====================================================================
# [FIM BLOCO] _normalizar_origem_aviso
# ====================================================================


# ====================================================================
# [BLOCO] BLOCO_UTIL
# [NOME] _gerar_ocorrencia_codigo
# [RESPONSABILIDADE] Gerar identificador sequencial global simples para a ocorrência
# ====================================================================
def _gerar_ocorrencia_codigo() -> str:
    padrao = re.compile(r"^OC-(\d{4})$")
    maior_numero = 0

    codigos_existentes = (
        db.session.query(Aviso.ocorrencia_codigo)
        .filter(Aviso.ocorrencia_codigo.isnot(None))
        .all()
    )

    for (codigo_existente,) in codigos_existentes:
        if not codigo_existente:
            continue

        match = padrao.match(str(codigo_existente).strip())
        if not match:
            continue

        numero = int(match.group(1))
        if numero > maior_numero:
            maior_numero = numero

    proximo = maior_numero + 1
    return f"OC-{proximo:04d}"


# ====================================================================
# [FIM BLOCO] _gerar_ocorrencia_codigo
# ====================================================================


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] _upsert_avisos_automaticos
# [RESPONSABILIDADE] Sincronizar avisos calculados com a tabela persistida
# ====================================================================
def _upsert_avisos_automaticos(avisos_calculados: List[Dict]) -> None:
    codigos_calculados = {a["codigo"] for a in avisos_calculados}

    avisos_existentes = (
        Aviso.query.filter(Aviso.tipo == "capacidade").order_by(Aviso.id.desc()).all()
    )

    mapa_existentes: Dict[str, Aviso] = {}
    for aviso_existente in avisos_existentes:
        if aviso_existente.codigo not in mapa_existentes:
            mapa_existentes[aviso_existente.codigo] = aviso_existente

        if not (aviso_existente.ocorrencia_codigo or "").strip():
            aviso_existente.ocorrencia_codigo = _gerar_ocorrencia_codigo()

    for payload in avisos_calculados:
        aviso = mapa_existentes.get(payload["codigo"])

        # Se já existe mas está resolvido, isso significa reabertura real:
        # nasce uma NOVA ocorrência
        if aviso and aviso.status == "resolvido":
            aviso = None

        if not aviso:
            aviso = Aviso(
                codigo=payload["codigo"],
                ocorrencia_codigo=_gerar_ocorrencia_codigo(),
                tipo="capacidade",
                titulo=payload["titulo"],
                descricao=payload["descricao"],
                severidade=payload["severidade"],
                status="novo",
                modelo=payload["modelo"],
                origem=payload["origem"],
                data_aviso=payload["data_aviso"],
                capacidade_atual=payload["capacidade_atual"],
                estoque_maximo=payload["estoque_maximo"],
            )
            db.session.add(aviso)
            continue

        if not (aviso.ocorrencia_codigo or "").strip():
            aviso.ocorrencia_codigo = _gerar_ocorrencia_codigo()

        aviso.titulo = payload["titulo"]
        aviso.descricao = payload["descricao"]
        aviso.severidade = payload["severidade"]
        aviso.modelo = payload["modelo"]
        aviso.origem = payload["origem"]
        aviso.data_aviso = aviso.data_aviso or payload["data_aviso"]
        aviso.capacidade_atual = payload["capacidade_atual"]
        aviso.estoque_maximo = payload["estoque_maximo"]

    for aviso in avisos_existentes:
        if aviso.codigo not in codigos_calculados and aviso.status != "resolvido":
            if not (aviso.ocorrencia_codigo or "").strip():
                aviso.ocorrencia_codigo = _gerar_ocorrencia_codigo()
            aviso.status = "resolvido"

    db.session.commit()


# ====================================================================
# [FIM BLOCO] _upsert_avisos_automaticos
# ====================================================================


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] _montar_historico_aviso
# [RESPONSABILIDADE] Transformar eventos persistidos em linhas de histórico para o template
# ====================================================================
def _montar_historico_aviso(aviso: Aviso) -> List[str]:
    linhas: List[str] = []

    if aviso.data_aviso:
        linhas.append(
            f"Evento: gerado automaticamente pelo sistema em {aviso.data_aviso.strftime('%d/%m/%Y %H:%M')}."
        )
    else:
        linhas.append("Evento: gerado automaticamente pelo sistema.")

    if (aviso.departamento_responsavel or "").strip():
        linhas.append(
            f"Evento: responsável definido como {(aviso.departamento_responsavel or '').strip().title()}."
        )

    eventos = (
        aviso.eventos.order_by(AvisoEvento.created_at.desc()).all()
        if hasattr(aviso.eventos, "order_by")
        else []
    )

    for evento in eventos:
        data_txt = (
            evento.created_at.strftime("%d/%m/%Y %H:%M") if evento.created_at else "—"
        )
        usuario = evento.usuario_nome or "—"

        if evento.tipo_evento == "lido":
            linhas.append(f"Evento: lido por {usuario} em {data_txt}.")
        elif evento.tipo_evento == "responsavel_definido":
            destino = (
                (
                    evento.destino
                    or aviso.departamento_responsavel
                    or "setor não informado"
                )
                .strip()
                .title()
            )
            linhas.append(
                f"Evento: responsável definido como {destino} por {usuario} em {data_txt}."
            )
        elif evento.tipo_evento == "comunicado":
            destino = (evento.destino or "setor não informado").strip().title()
            linhas.append(
                f"Evento: comunicado ao setor {destino} por {usuario} em {data_txt}."
            )
        elif evento.tipo_evento == "status_alterado":
            observacao = (evento.observacao or "").strip()
            if observacao:
                linhas.append(f"Evento: {observacao} por {usuario} em {data_txt}.")
            else:
                linhas.append(f"Evento: status alterado por {usuario} em {data_txt}.")
        elif evento.tipo_evento == "encerrado":
            linhas.append(f"Evento: encerrado por {usuario} em {data_txt}.")
        else:
            observacao = (
                evento.observacao or evento.tipo_evento or "ação registrada"
            ).strip()
            linhas.append(f"Evento: {observacao} por {usuario} em {data_txt}.")

    return linhas


# ====================================================================
# [FIM BLOCO] _montar_historico_aviso
# ====================================================================


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] _montar_payload_aviso
# [RESPONSABILIDADE] Converter Aviso persistido em payload pronto para a tela
# ====================================================================
def _montar_payload_aviso(aviso: Aviso, pecas_criticas: List[Dict]) -> Dict:
    tipo_label = _rotulo_tipo_aviso(aviso.tipo)
    origem = _normalizar_origem_aviso(aviso.origem, aviso.tipo)

    return {
        "codigo": aviso.codigo,
        "ocorrencia_codigo": aviso.ocorrencia_codigo,
        "tipo": aviso.tipo,
        "tipo_label": tipo_label,
        "severidade": aviso.severidade,
        "titulo": aviso.titulo,
        "descricao": aviso.descricao,
        "modelo": aviso.modelo,
        "origem": origem,
        "data_aviso": aviso.data_aviso,
        "lido_por_nome": aviso.lido_por_nome,
        "lido_em": aviso.lido_em,
        "status": aviso.status,
        "capacidade_atual": aviso.capacidade_atual,
        "estoque_maximo": aviso.estoque_maximo,
        "pecas_criticas": pecas_criticas,
        "historico": _montar_historico_aviso(aviso),
    }


# ====================================================================
# [FIM BLOCO] _montar_payload_aviso
# ====================================================================


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] montar_painel_avisos
# [RESPONSABILIDADE] Consolidar dados da central de avisos para tela e APIs
# ====================================================================
def montar_painel_avisos() -> Dict:
    avisos_calculados: List[Dict] = listar_avisos_capacidade()
    _upsert_avisos_automaticos(avisos_calculados)

    mapa_pecas = {a["codigo"]: a.get("pecas_criticas", []) for a in avisos_calculados}

    avisos_db = (
        Aviso.query.filter(Aviso.tipo == "capacidade")
        .order_by(Aviso.status.asc(), Aviso.data_aviso.desc())
        .all()
    )

    avisos: List[Dict] = [
        _montar_payload_aviso(
            aviso=aviso,
            pecas_criticas=mapa_pecas.get(aviso.codigo, []),
        )
        for aviso in avisos_db
    ]

    ativos = [a for a in avisos if a.get("status") != "resolvido"]

    return {
        "avisos": avisos,
        "avisos_qtd": len(ativos),
        "tem_avisos": len(ativos) > 0,
    }


# ====================================================================
# [FIM BLOCO] montar_painel_avisos
# ====================================================================


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] montar_card_home_producao
# [RESPONSABILIDADE] Gerar payload resumido para o card AVISOS da home da produção
# ====================================================================
def montar_card_home_producao() -> Dict:
    painel = montar_painel_avisos()
    return {
        "avisos_qtd": painel["avisos_qtd"],
        "avisos_ativos": painel["tem_avisos"],
    }


# ====================================================================
# [FIM BLOCO] montar_card_home_producao
# ====================================================================
