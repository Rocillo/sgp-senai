# ====================================================================
# [BLOCO] MÓDULO
# [NOME] indicadores_models
# [RESPONSABILIDADE] Definir modelos ORM das tabelas de indicadores gerenciais
# ====================================================================

from datetime import datetime

from app import db


# ====================================================================
# [BLOCO] CLASSE
# [NOME] GPProductionAlarm
# [RESPONSABILIDADE] Registrar histórico de alarmes de falta de componente na produção
# ====================================================================
class GPProductionAlarm(db.Model):
    __tablename__ = "gp_component_alarm"

    id = db.Column(db.Integer, primary_key=True)
    occurred_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)

    bench_id = db.Column(db.String(10), nullable=False)
    modelo = db.Column(db.String(50), nullable=False)
    serial = db.Column(db.String(64), nullable=True)

    component_code = db.Column(db.String(50), nullable=False)
    component_desc = db.Column(db.String(120), nullable=True)

    required_qty = db.Column(db.Integer, nullable=True)
    available_qty = db.Column(db.Integer, nullable=True)

    downtime_min = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="open")
    source = db.Column(db.String(30), nullable=False, default="montagem_api")

    details_json = db.Column(db.JSON, nullable=True)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# ====================================================================
# [FIM BLOCO] GPProductionAlarm
# ====================================================================


# ====================================================================
# [BLOCO] CLASSE
# [NOME] GPWorkingCalendar
# [RESPONSABILIDADE] Representar calendário operacional de dias úteis, feriados e exceções
# ====================================================================
class GPWorkingCalendar(db.Model):
    __tablename__ = "work_calendar"

    dia = db.Column(db.Date, primary_key=True)
    eh_dia_util = db.Column(db.Boolean, nullable=False, default=True)
    descricao = db.Column(db.String(120), nullable=True)
    turno_minutos_planejados = db.Column(db.Integer, nullable=False, default=480)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# ====================================================================
# [FIM BLOCO] GPWorkingCalendar
# ====================================================================


# ====================================================================
# MAPA DO ARQUIVO
# --------------------------------------------------------------------
# CLASSE: GPProductionAlarm
# CLASSE: GPWorkingCalendar
# ====================================================================
