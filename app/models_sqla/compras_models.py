"""SQLAlchemy models for Purchase Requisitions module.

This module contains the database models for the Purchase Requisitions system,
including requisitions, items, and status history tracking.
"""

from datetime import datetime
from app import db


# ====================================================================
# [BLOCO] CLASSE
# [NOME] CompraRequisicao
# [RESPONSABILIDADE] Representar requisições de compras com solicitante, status e prazos
# ====================================================================
class CompraRequisicao(db.Model):
    __tablename__ = "compras_requisicoes"

    id = db.Column(db.Integer, primary_key=True)
    numero_requisicao = db.Column(
        db.String(50), unique=True, nullable=False, index=True
    )
    solicitante_id = db.Column(db.Integer, nullable=True, index=True)
    solicitante_nome_snapshot = db.Column(db.String(100), nullable=True)
    setor = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(50), nullable=False, default="SOLICITADA", index=True)
    urgencia = db.Column(db.String(20), nullable=True)
    prazo_desejado = db.Column(db.Date, nullable=True)
    data_solicitacao = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, index=True
    )
    observacao_geral = db.Column(db.Text, nullable=True)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=True, onupdate=datetime.utcnow)

    def as_dict(self) -> dict:
        """Serializa o objeto para dicionário."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# ====================================================================
# [FIM BLOCO] CompraRequisicao
# ====================================================================


# ====================================================================
# [BLOCO] CLASSE
# [NOME] CompraRequisicaoItem
# [RESPONSABILIDADE] Representar itens de requisição com peças, quantidades e referências
# ====================================================================
class CompraRequisicaoItem(db.Model):
    __tablename__ = "compras_requisicao_itens"

    id = db.Column(db.Integer, primary_key=True)
    requisicao_id = db.Column(
        db.Integer, db.ForeignKey("compras_requisicoes.id"), nullable=False, index=True
    )
    tipo_item = db.Column(db.String(50), nullable=False, index=True)
    peca_id = db.Column(db.Integer, nullable=True, index=True)
    codigo_pneumark_snapshot = db.Column(db.String(50), nullable=True)
    descricao_snapshot = db.Column(db.String(200), nullable=True)
    descricao_digitada = db.Column(db.String(200), nullable=True)
    quantidade = db.Column(db.Numeric(12, 3), nullable=False)
    unidade = db.Column(db.String(20), nullable=True)
    estoque_atual_snapshot = db.Column(db.Numeric(12, 3), nullable=True)
    ultimo_preco_referencia = db.Column(db.Numeric(12, 2), nullable=True)
    link_referencia_principal = db.Column(db.String(500), nullable=True)
    observacao_item = db.Column(db.Text, nullable=True)
    # Campos de parecer automático
    parecer_status = db.Column(db.String(50), nullable=True)
    parecer_nivel = db.Column(db.String(20), nullable=True)
    parecer_mensagem = db.Column(db.Text, nullable=True)
    parecer_quantidade_sugerida = db.Column(db.Integer, nullable=True)
    parecer_excesso_atual = db.Column(db.Integer, nullable=True)
    decisao_contra_recomendacao = db.Column(db.Boolean, nullable=False, default=False)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=True, onupdate=datetime.utcnow)

    def as_dict(self) -> dict:
        """Serializa o objeto para dicionário."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# ====================================================================
# [FIM BLOCO] CompraRequisicaoItem
# ====================================================================


# ====================================================================
# [BLOCO] CLASSE
# [NOME] CompraHistoricoStatus
# [RESPONSABILIDADE] Registrar histórico de mudanças de status das requisições com auditoria
# ====================================================================
class CompraHistoricoStatus(db.Model):
    __tablename__ = "compras_historico_status"

    id = db.Column(db.Integer, primary_key=True)
    requisicao_id = db.Column(
        db.Integer, db.ForeignKey("compras_requisicoes.id"), nullable=False, index=True
    )
    status_anterior = db.Column(db.String(50), nullable=True)
    status_novo = db.Column(db.String(50), nullable=False)
    usuario_id = db.Column(db.Integer, nullable=True)
    usuario_nome_snapshot = db.Column(db.String(100), nullable=True)
    data_evento = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, index=True
    )
    comentario = db.Column(db.Text, nullable=True)
    origem_evento = db.Column(db.String(50), nullable=False, default="sistema")

    def as_dict(self) -> dict:
        """Serializa o objeto para dicionário."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# ====================================================================
# [FIM BLOCO] CompraHistoricoStatus
# ====================================================================


# ====================================================================
# MAPA DO ARQUIVO
# --------------------------------------------------------------------
# CLASSE: CompraRequisicao
# CLASSE: CompraRequisicaoItem
# CLASSE: CompraHistoricoStatus
# ====================================================================
