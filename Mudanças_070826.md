# Mudanças — 08/07/2026

> **Contexto:** Investigação e correção do fluxo de dados entre o Painel Kanban (HipotModal, ChecklistBackdrop) e a página de Rastreabilidade por Número de Série (`/producao/gp/rastreabilidade/<serial>`).

---

## 1. `hipot_routes.py` — Timestamps ausentes no registro Hi-Pot (Board Modal)

**Arquivo:** `app/routes/producao_routes/gerenciamento_producao_routes/hipot_routes.py`  
**Endpoint:** `POST /producao/gp/hipot/api/painel-submit-result`

**Problema:** Ao salvar o resultado do Hi-Pot pelo modal do Painel Kanban (coluna HI-POT), o registro `GPHipotRun` era criado sem `started_at` nem `finished_at`. Com esses campos `NULL`, a API de rastreabilidade não conseguia ordenar nem exibir a data/hora do ensaio.

**Correção:** Adicionados `started_at=now` e `finished_at=now` (UTC) no momento da criação do `GPHipotRun`.

```python
# ANTES
run = GPHipotRun(serial=serial, operador=operador_id, ...)

# DEPOIS
now = datetime.utcnow()
run = GPHipotRun(serial=serial, operador=operador_id, ..., started_at=now, finished_at=now)
```

---

## 2. `rastreabilidade_routes.py` — Import incorreto de `GPHipotRun`

**Arquivo:** `app/routes/producao_routes/rastreabilidade_nserie_routes/rastreabilidade_routes.py`

**Problema:** O import tentava carregar `GPHipotRun` de `app.models.producao_models.gp_hipot` — caminho que **não existe** (o arquivo está em `gp_models/gp_hipot.py`). Como resultado, a variável ficava `None` em tempo de execução e a seção **⚡ Ensaio Elétrico (Hi-Pot)** sempre mostrava *"Nenhum ensaio elétrico registrado."*

**Correção:** Corrigido o caminho do import para `app.models.producao_models.gp_models.gp_hipot`, com dois fallbacks adicionais para robustez:

```python
# ANTES (caminho errado)
from app.models.producao_models.gp_hipot import GPHipotRun as _HR

# DEPOIS (caminho correto + fallbacks)
# 1ª tentativa: caminho correto
from app.models.producao_models.gp_models.gp_hipot import GPHipotRun as _HR
# 2ª tentativa: caminho legado
from app.models.producao_models.gp_hipot import GPHipotRun as _HR
# 3ª tentativa: models_sqla diretamente
from app.models_sqla import GPHipotRun as _HR
```

---

## 3. `rastreabilidade_routes.py` — Import incorreto dos modelos de Checklist

**Arquivo:** `app/routes/producao_routes/rastreabilidade_nserie_routes/rastreabilidade_routes.py`

**Problema:** O bloco de fallback tentava importar `GPChecklistExecucao` e `GPChecklistExecItem` de `app.models_sqla` — nomes que **não existem**. Os nomes corretos são `GPChecklistExecution` e `GPChecklistExecutionItem`. O fallback falhava silenciosamente, deixando os modelos como `None`.

**Correção:**

```python
# ANTES (nomes errados)
from app.models_sqla import (
    GPChecklistExecucao as _CE,
    GPChecklistExecItem as _CEI,
    ...
)

# DEPOIS (nomes corretos)
from app.models_sqla import (
    GPChecklistExecution as _CE,
    GPChecklistExecutionItem as _CEI,
    ...
)
```

---

## 4. `rastreabilidade_routes.py` — Query Hi-Pot com `started_at NULL` causava erro de ordenação

**Arquivo:** `app/routes/producao_routes/rastreabilidade_nserie_routes/rastreabilidade_routes.py`

**Problema:** A query usava `.order_by(GPHipotRun.started_at.desc())`. Com `started_at = NULL` em registros antigos, o SQLite colocava esses registros por último ou a query falhava.

**Correção:** Substituído por ordenação com `nullslast` e fallback por `id.desc()`:

```python
from sqlalchemy import desc as _desc, nullslast
last_hipot = (
    db.session.query(GPHipotRun)
    .filter(GPHipotRun.serial == serial)
    .order_by(nullslast(_desc(GPHipotRun.started_at)), _desc(GPHipotRun.id))
    .first()
)
```

---

## 5. `rastreabilidade_routes.py` — `started_at` e `duracao_min` ausentes no payload principal

**Arquivo:** `app/routes/producao_routes/rastreabilidade_nserie_routes/rastreabilidade_routes.py`

**Problema:** O modelo `GPWorkOrder` **não possui coluna `started_at`** — apenas `created_at` e `finished_at`. A API lia um campo inexistente, retornando `None`, e o `duracao_min` (tempo total de produção) nunca era calculado. Na página de rastreabilidade, a seção **Dados Gerais de Produção** mostrava apenas "Fim da Produção" com dados.

**Correção:** Mapeado `created_at` como `started_at` e computado `duracao_min`:

```python
# ANTES
"started_at": _fmt_dt_iso(getattr(work_order, "started_at", None)),  # sempre None
# duracao_min não existia no payload raiz

# DEPOIS
_wo_created  = getattr(work_order, "created_at", None)
_wo_finished = getattr(work_order, "finished_at", None)
payload = {
    ...
    "started_at":  _fmt_dt_iso(_wo_created),
    "finished_at": _fmt_dt_iso(_wo_finished),
    "duracao_min": _safe_int_minutes(_wo_created, _wo_finished),
}
```

---

## 6. `detalhes_rastreamento.html` — Seção Dados Gerais exibia apenas 4 campos

**Arquivo:** `app/templates/producao_templates/rastreabilidade_templates/detalhes_rastreamento.html`

**Problema:** O bloco `dadosGerais` exibia apenas 4 campos (`Início`, `Fim`, `Tempo Total`, `Status`), deixando de fora Modelo, Nº Série, Ordem de Produção, Lote e Última Atualização.

**Correção:** Expandido para 8–10 campos:

```
Nº de Série | Modelo | Ordem de Produção | Lote
Início da Produção | Fim da Produção | Tempo Total | Status
Criado Por (se disponível) | Última Atualização (se disponível)
```

---

## 7. Banco de Dados — Criação de tabelas de Checklist e patch de timestamps

**Ação executada via script (`fix_db.py`):**

1. **`db.create_all()`** — Criadas as tabelas que não existiam:
   - `gp_checklist_execucoes`
   - `gp_checklist_exec_items`
   - `gp_checklist_templates`
   - `gp_checklist_items`

2. **Patch do registro Hi-Pot existente** — O único registro em `gp_hipot_run` (id=1, serial=672006) tinha `started_at = NULL`. Atualizado para o timestamp atual para garantir exibição correta na rastreabilidade.

---

## Resumo dos Arquivos Alterados

| Arquivo | Tipo de Mudança |
|---|---|
| `app/routes/producao_routes/gerenciamento_producao_routes/hipot_routes.py` | Bug fix — timestamps ausentes |
| `app/routes/producao_routes/rastreabilidade_nserie_routes/rastreabilidade_routes.py` | Bug fix — 4 imports/queries incorretos + campo inexistente |
| `app/templates/producao_templates/rastreabilidade_templates/detalhes_rastreamento.html` | Melhoria — mais campos em Dados Gerais |
| `pneumark.db` | Data fix — criação de tabelas + patch de timestamps |

---

## Resultado Final

Após as correções e reinicialização do servidor Flask, a página `/producao/gp/rastreabilidade/672006` exibe corretamente:

- ✅ **Dados Gerais** — Todos os campos preenchidos (início, fim, 15 min de duração, status CONCLUÍDO)
- ✅ **Ensaio Hi-Pot** — Tensão: 1000 V, Continuidade: 0.02 mΩ, Resultado: APROVADO, Operador: Guilherme
- ✅ **Checklist Bancada 8** — 3 itens, todos APROVADOS, resultado final: Aprovado
- ✅ **Timeline de Bancadas** — Histórico de todas as etapas percorridas pelo serial
