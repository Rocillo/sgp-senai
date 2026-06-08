# ====================================================================
# [BLOCO] MÓDULO
# [NOME] periodo_service
# [RESPONSABILIDADE] Normalizar períodos e gerar buckets de data para indicadores
# ====================================================================

from datetime import date, datetime, time, timedelta
from typing import List, Tuple
from zoneinfo import ZoneInfo

TIMEZONE_LOCAL = ZoneInfo("America/Sao_Paulo")


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] hoje_local
# [RESPONSABILIDADE] Retornar data atual no timezone local da operação
# ====================================================================
def hoje_local() -> date:
    return datetime.now(TIMEZONE_LOCAL).date()


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] normalizar_periodo
# [RESPONSABILIDADE] Validar datas e retornar período normalizado
# ====================================================================
def normalizar_periodo(data_inicio_raw=None, data_fim_raw=None) -> Tuple[date, date]:
    if not data_inicio_raw or not data_fim_raw:
        hoje = hoje_local()
        return hoje.replace(day=1), hoje

    try:
        data_inicio = datetime.strptime(data_inicio_raw, "%Y-%m-%d").date()
        data_fim = datetime.strptime(data_fim_raw, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("Use o formato YYYY-MM-DD para data_inicio e data_fim.")

    if data_inicio > data_fim:
        raise ValueError("data_inicio não pode ser maior que data_fim.")

    return data_inicio, data_fim


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] limites_datetime_periodo
# [RESPONSABILIDADE] Gerar limite inicial inclusivo e final exclusivo para consultas
# ====================================================================
def limites_datetime_periodo(
    data_inicio: date, data_fim: date
) -> Tuple[datetime, datetime]:
    inicio = datetime.combine(data_inicio, time.min).replace(tzinfo=TIMEZONE_LOCAL)
    fim_exclusivo = datetime.combine(
        data_fim + timedelta(days=1),
        time.min,
    ).replace(tzinfo=TIMEZONE_LOCAL)

    return inicio, fim_exclusivo


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] meses_periodo
# [RESPONSABILIDADE] Gerar buckets mensais YYYY-MM entre data inicial e final
# ====================================================================
def meses_periodo(data_inicio: date, data_fim: date) -> List[str]:
    atual = date(data_inicio.year, data_inicio.month, 1)
    limite = date(data_fim.year, data_fim.month, 1)

    meses = []

    while atual <= limite:
        meses.append(atual.strftime("%Y-%m"))

        if atual.month == 12:
            atual = date(atual.year + 1, 1, 1)
        else:
            atual = date(atual.year, atual.month + 1, 1)

    return meses


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] dias_periodo
# [RESPONSABILIDADE] Gerar lista contínua de datas entre início e fim
# ====================================================================
def dias_periodo(data_inicio: date, data_fim: date) -> List[date]:
    dias = []
    atual = data_inicio

    while atual <= data_fim:
        dias.append(atual)
        atual += timedelta(days=1)

    return dias


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] dias_uteis_fallback
# [RESPONSABILIDADE] Gerar dias úteis padrão segunda a sexta
# ====================================================================
def dias_uteis_fallback(data_inicio: date, data_fim: date) -> List[date]:
    return [dia for dia in dias_periodo(data_inicio, data_fim) if dia.weekday() < 5]


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] mes_ref
# [RESPONSABILIDADE] Converter data/datetime em chave mensal YYYY-MM
# ====================================================================
def mes_ref(valor) -> str:
    if isinstance(valor, datetime):
        return valor.strftime("%Y-%m")

    if isinstance(valor, date):
        return valor.strftime("%Y-%m")

    return str(valor)[:7]


# ====================================================================
# MAPA DO ARQUIVO
# --------------------------------------------------------------------
# FUNÇÃO: hoje_local
# FUNÇÃO: normalizar_periodo
# FUNÇÃO: limites_datetime_periodo
# FUNÇÃO: meses_periodo
# FUNÇÃO: dias_periodo
# FUNÇÃO: dias_uteis_fallback
# FUNÇÃO: mes_ref
# ====================================================================
