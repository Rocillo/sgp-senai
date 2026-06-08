# app\models\avisos_models\aviso_evento.py
from datetime import datetime
from app.models.avisos_models.aviso import Aviso
from app import db


# ====================================================================
# [BLOCO] CLASSE
# [NOME] AvisoEvento
# [RESPONSABILIDADE] Persistir histórico operacional de leitura e comunicação dos avisos
# ====================================================================
class AvisoEvento(db.Model):
    __tablename__ = "avisos_eventos"

    id = db.Column(db.Integer, primary_key=True)

    aviso_id = db.Column(
        db.Integer,
        db.ForeignKey("avisos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    tipo_evento = db.Column(db.String(30), nullable=False, index=True)
    usuario_id = db.Column(db.Integer, nullable=True)
    usuario_nome = db.Column(db.String(120), nullable=True)

    destino = db.Column(db.String(50), nullable=True)
    observacao = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    aviso = db.relationship(Aviso, back_populates="eventos")


# ====================================================================
# [FIM BLOCO] AvisoEvento
# ====================================================================


#
