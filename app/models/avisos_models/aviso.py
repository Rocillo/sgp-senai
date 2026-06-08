# app\models\avisos_models\aviso.py
from datetime import datetime

from app import db


# ====================================================================
# [BLOCO] CLASSE
# [NOME] Aviso
# [RESPONSABILIDADE] Persistir aviso principal da central de avisos da produção
# ====================================================================
class Aviso(db.Model):
    __tablename__ = "avisos"

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(80), unique=True, nullable=False, index=True)
    ocorrencia_codigo = db.Column(db.String(30), unique=True, nullable=True, index=True)

    tipo = db.Column(db.String(50), nullable=False, default="capacidade")
    titulo = db.Column(db.String(255), nullable=False)
    descricao = db.Column(db.Text, nullable=False)

    severidade = db.Column(db.String(20), nullable=False, default="critico")
    status = db.Column(db.String(20), nullable=False, default="novo")

    modelo = db.Column(db.String(50), nullable=True, index=True)
    origem = db.Column(db.String(80), nullable=True)

    departamento_responsavel = db.Column(db.String(50), nullable=True, index=True)

    data_aviso = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    capacidade_atual = db.Column(db.Integer, nullable=True)
    estoque_maximo = db.Column(db.Integer, nullable=True)

    lido_por_user_id = db.Column(db.Integer, nullable=True)
    lido_por_nome = db.Column(db.String(120), nullable=True)
    lido_em = db.Column(db.DateTime, nullable=True)

    resolvido_por_user_id = db.Column(db.Integer, nullable=True)
    resolvido_por_nome = db.Column(db.String(120), nullable=True)
    resolvido_em = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    eventos = db.relationship(
        "AvisoEvento",
        back_populates="aviso",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    destinatarios = db.relationship(
        "AvisoDestinatario",
        back_populates="aviso",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )


# ====================================================================
# [FIM BLOCO] Aviso
# ====================================================================
