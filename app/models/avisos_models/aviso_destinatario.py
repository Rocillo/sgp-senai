from datetime import datetime

from app import db


# ====================================================================
# [BLOCO] CLASSE
# [NOME] AvisoDestinatario
# [RESPONSABILIDADE] Persistir setores comunicados para cada aviso
# ====================================================================
class AvisoDestinatario(db.Model):
    __tablename__ = "avisos_destinatarios"

    id = db.Column(db.Integer, primary_key=True)

    aviso_id = db.Column(
        db.Integer,
        db.ForeignKey("avisos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    setor = db.Column(db.String(30), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default="comunicado")

    comunicado_por_user_id = db.Column(db.Integer, nullable=True)
    comunicado_por_nome = db.Column(db.String(120), nullable=True)
    comunicado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    aviso = db.relationship("Aviso", back_populates="destinatarios")

    __table_args__ = (
        db.UniqueConstraint("aviso_id", "setor", name="uq_aviso_destinatario_setor"),
    )


# ====================================================================
# [FIM BLOCO] AvisoDestinatario
# ====================================================================
