# Relatório Técnico de Integração - HIPOT & SGP (Pneumark / SEBRATECTEC)

Este documento registra todas as alterações arquiteturais e de código realizadas no ecossistema **SGP (Sistema de Gestão de Produção)** e no coletor desktop **HIPOT** para viabilizar a integração e sincronização automática de dados. 

Este relatório servirá como baseline para a elaboração do relatório final do projeto de integração para a empresa Pneumark.

---

## 1. Contexto e Objetivo Geral

A inspeção inicial revelou duas metades isoladas:
1. **SGP (Web/Flask)**: Centralizador da linha de produção, controle de bancadas (Kanban) e timeline de rastreabilidade.
2. **HIPOT (Desktop/PySide6)**: Aplicativo local que realiza leitura serial de ensaios elétricos de bancada e grava localmente em `hipot.db`.

O objetivo deste ciclo de desenvolvimento foi **conectar as duas bases de dados** de forma segura e resiliente. Optou-se por uma arquitetura com **Fila Local Offline (Resiliência) + Sincronização via API HTTP Ingestora**. Isso garante que:
- O operador continue testando produtos mesmo se a rede ou o servidor central web estiverem temporariamente fora do ar.
- As leituras analíticas completas (corrente de fuga de isolamento e resistência de aterramento) sejam extraídas e enviadas para o servidor central SGP.
- O painel Kanban de produção avance de estágio automaticamente quando o teste Hi-Pot for aprovado.

---

## 2. Alterações Realizadas

### A. Banco de Dados Local do Coletor (`collector_hipot_post/database.py`)
- **Migração Dinâmica de Schema**: Atualização da função `criar_tabela()` para inspecionar as colunas da tabela `testes_hipot` e injetar dinamicamente a coluna `sincronizado` (tipo `INTEGER`, default `0`) via `ALTER TABLE` caso ela não exista. Isso protege os dados históricos existentes.
- **Marcação de Status**: Ajuste na função `salvar_teste()` para registrar novos ensaios com o status `sincronizado = 0`. O ID único do teste inserido passou a ser retornado (`cursor.lastrowid`).
- **Funções de Fila Local**:
  - `obter_testes_pendentes()`: Consulta todos os registros onde `sincronizado = 0` ou nulo.
  - `marcar_como_sincronizado(id_teste)`: Atualiza o status de sincronização de um ensaio específico no banco local para `1` (Sucesso).

### B. Interface do Coletor Desktop (`collector_hipot_post/gui.py` & `sync_worker.py`)
- **Configuração de Endpoint**: Implementação do arquivo local `config.json` que armazena a URL base do servidor central SGP (`sgp_url`), tornando o aplicativo configurável para diferentes ambientes (desenvolvimento, staging ou produção).
- **Trabalho Assíncrono (`SyncWorker`)**:
  - Implementação de uma thread em segundo plano (`QThread`) para processamento da fila local de sincronização.
  - A thread lê os testes pendentes no banco local e realiza requisições HTTP `POST` utilizando a biblioteca padrão do Python (`urllib`), o que elimina a necessidade de instalar dependências de rede externas no executável compilado.
  - O loop acorda a cada 30 segundos ou imediatamente após a gravação de um novo teste no banco (`self.sync_worker.trigger_sync()`).
- **Feedback Visual na Interface**:
  - Inclusão do rótulo `self.sync_label` na área de status superior da tela principal.
  - Informa em tempo real o status de sincronização:
    - 🟢 *Verde*: Banco local totalmente sincronizado.
    - 🟡 *Amarelo*: Conectando ou processando pendências (com contagem de fila).
    - 🔴 *Vermelho*: Servidor offline ou falha de comunicação (mantendo fila local intacta).

### C. Backend do Servidor Central SGP (`app/routes/producao_routes/gerenciamento_producao_routes/hipot_routes.py`)
- **Correção de Bug de Contrato**: Correção de um bug crítico na rota `/api/result` que causava respostas `500 Internal Server Error` (tentativa de acessar atributos de objeto em um dicionário Python retornado pelo serviço).
- **Ingestão Completa de Ensaios**:
  - A rota passou a receber o payload completo do coletor contendo metadados (operador, porta serial, baudrate, logs brutos do instrumento e carimbo de tempo).
  - Implementação de lógica de idempotência (deduplicação) baseada em número de série (`serial`) e timestamp (`started_at`) do ensaio original.
- **Parser de Relatórios Brutos**:
  - Criação da função `_parse_relatorio_hipot()` para interpretar a string de logs enviada pelo coletor (ex: `"ENTRAN | HGF148 | 1.25 mA | 0.05 mR | APR"`).
  - Extrai automaticamente valores numéricos como a Corrente de Fuga (`hp_ileak_ma` em mA) e a Resistência de Aterramento (`gb_r_mohm` em mR/mΩ), bem como o modelo do produto.
- **Persistência Estruturada**: Gravação completa de todas as métricas detalhadas em um novo registro do modelo `GPHipotRun` no banco de dados centralizado do SGP.
- **Integração de Kanban de Bancada**:
  - Ao processar e aprovar o teste via API, a etapa atual correspondente à bancada de ensaios elétricos (B5) é fechada automaticamente no banco.
  - Chama o serviço de transição `aplicar_resultado_hipot()` que atualiza a ordem de produção e avança o produto para a próxima bancada ativa da rota (ex: montagem final / embalagem).

### D. Integração de Atalho no Painel de Produção (Board Kanban B5)
- **Nome do Entry Point Renomeado**: Renomeado `main.py` da pasta `collector_hipot_post` para `collector.py` para evitar colisões de nomenclatura com o `main.py` da raiz do SGP e permitir uma identificação inequívoca de cada aplicação.
- **Botão de Acesso Rápido no Kanban**: Inserção de um botão `"🔌 Iniciar Coletor Desktop (Hi-Pot)"` dentro do modal de detalhes da bancada Hi-Pot (B5) no template `board.html`.
- **Comando de Inicialização via API**: Criação da rota `/api/launch` no backend Flask (`hipot_routes.py`) que usa `subprocess.Popen` para inicializar em segundo plano a aplicação PySide6 no Windows host local.
- **Pré-preenchimento Automático do Serial**: Configuração do construtor de `HipotWindow` em `gui.py` para receber parâmetros de linha de comando (`sys.argv`). Ao clicar no botão no SGP, o número de série da peça atual é passado como argumento e pré-preenchido automaticamente na tela do coletor desktop.

### E. Melhorias e Integração de Checklist (Bancada B8 e Kanban)
- **Campos de Controle de Tempo**: Adicionado suporte para os campos `min_s` (tempo mínimo em segundos) e `max_s` (tempo máximo em segundos) nos itens do checklist (`app/static/js/gp_checklist/exec.js`). 
- **Desbloqueio com Tempo Mínimo**: A conclusão dos itens do checklist agora respeita o campo `min_s` de forma que o botão de aprovação/reprovação permaneça desabilitado até que o tempo mínimo de teste configurado para a tarefa tenha decorrido.
- **Banner de Status no Modal**: Inclusão de um banner persistente de status de execução (`#checklistActiveTimerBanner`) no topo do checklist modal (`board.html`), mostrando contagens regressivas de tempo mínimo e feedback visual sobre o estado atual do teste (ex: aguardando tempo mínimo, tarefa liberada, checklist concluído).
- **Integração com Fluxo Kanban (Bancada B8)**: O salvamento das execuções de checklist (`gp_checklist_api.py`) foi integrado ao fluxo do painel SGP:
  - Cria/atualiza e encerra a etapa `GPWorkStage` na bancada B8 com o resultado do checklist (`APR` ou `REP`).
  - Avança a ordem de produção para a etapa subsequente utilizando o serviço `advance_after_finish`.
  - Conclui a ordem de produção definindo o status como `done` caso a próxima etapa seja a finalização, registrando a saída do produto acabado no controle de estoque.
- **Tratamento Amigável de Erros**: Implementação da função `friendlyErrorText` no frontend para mapear falhas de comunicação e erros de validação de dados em mensagens claras e localizadas ao operador.

### F. Outros Ajustes Operacionais
- **Codificação de Dependências**: Conversão do arquivo `requirements.txt` da raiz do projeto SGP de **UTF-16LE** para **UTF-8**, resolvendo incompatibilidades com ferramentas de build e automações.

---

## 3. Validação e Testes Executados

Para garantir o perfeito funcionamento da integração, foram criadas suites de testes locais executadas no ambiente do projeto:

### 1. Teste de Banco Local (`test_integration.py`)
Valida o ciclo completo da fila local de banco de dados:
- Criação e alteração do banco local adicionando a nova coluna.
- Inserção de registro pendente.
- Leitura de fila de sincronização.
- Atualização para sincronizado e esvaziamento da fila local.
- **Status**: **Aprovado (100% dos testes executados com sucesso)**.

### 2. Teste de API do Servidor (`test_backend.py`)
Simula a chamada de rede a partir da aplicação Flask sob um contexto de teste controlado:
- Criação de uma ordem de produção e abertura da etapa B5 na base SGP.
- Envio de JSON contendo dados brutos e leituras seriais formatadas.
- Confirmação de persistência no modelo `GPHipotRun` com extração precisa de valores float (`1.45 mA` e `0.08 mR`).
- Confirmação de encerramento da etapa de fabricação elétro-eletrônica e avanço do produto no roteiro.
- Validação do tratamento de tentativas de requisições duplicadas.
- **Status**: **Aprovado (100% dos testes executados com sucesso)**.

### 3. Teste do Inicializador Desktop (`test_launch.py`)
Valida o disparo do aplicativo desktop a partir de endpoints Flask:
- Chamada HTTP POST simulando o Kanban com Serial Number.
- Confirmação de spawn assíncrono do processo `collector.py` com o argumento de pré-preenchimento.
- **Status**: **Aprovado (100% dos testes executados com sucesso)**.

---

## 4. Benefícios Arquiteturais para a Pneumark

1. **Garantia de Não-Interrupção (Resiliência)**: A operação fabril nas bancadas elétricas não é interrompida mesmo na ausência de sinal de internet/rede local.
2. **Auditabilidade e Rastreabilidade**: Dados brutos do ensaio (corrente de fuga de isolamento e resistência) ficam atrelados ao número de série do produto de forma centralizada e permanente para auditorias de qualidade.
3. **Segurança de TI**: Nenhuma credencial de banco de dados direto (como PostgreSQL) precisa ser exposta nos computadores industriais da fábrica. Toda a comunicação ocorre sobre o protocolo seguro HTTP de forma controlada pela API.
4. **Agilidade Operacional**: O operador não precisa digitar ou re-escanear o número de série da peça na bancada Hi-Pot; a abertura automática pré-preenche o dado, acelerando a fabricação e eliminando erros humanos.

---

## 5. Diagnóstico e Resolução de Problemas (Troubleshooting)

### A. Erro: "Não foi possível enviar comando para o servidor local"
Este erro ocorre no navegador do operador ao clicar no botão "Abrir Coletor Desktop". As causas comuns e resoluções são:

1. **Servidor Flask Inativo**:
   - **Causa**: O servidor central SGP não está em execução no host local (ex: porta `5000` fechada), interrompendo a comunicação da API.
   - **Resolução**: Inicie o servidor SGP executando `python main.py` no diretório raiz do projeto. Verifique no terminal se o status diz `Running on http://127.0.0.1:5000`.
   
2. **Desvio de Endereço/Porta**:
   - **Causa**: O servidor está rodando em uma porta ou IP diferente do qual o painel está sendo acessado.
   - **Resolução**: Acesse o painel pelo mesmo endereço de escuta do servidor (geralmente `http://127.0.0.1:5000/producao/gp/painel/`).

3. **Ambiente Isolado (Docker / Nuvem)**:
   - **Causa**: Se o servidor SGP estiver hospedado remotamente na nuvem ou dentro de um container Docker sem acesso direto ao host local, o servidor não conseguirá interagir com o subsistema do sistema operacional Windows para abrir a interface gráfica do coletor.
   - **Resolução**: Em deploys remotos de produção, deve-se adotar o protocolo customizado do Windows (`hipot://`) para que o próprio navegador instrua o sistema operacional a abrir o coletor local, em vez de depender da API de loopback do servidor central.

4. **Melhorias de Diagnóstico Implementadas**:
    - O código JavaScript no arquivo `board.html` foi atualizado para capturar a mensagem detalhada da exceção do navegador. Se o erro persistir, o sistema mostrará a mensagem exata do erro de rede (ex: `Failed to fetch`, `Connection Refused`) em um balão de alerta (toast) na interface, facilitando o diagnóstico instantâneo.

---

## 6. Passo a Passo de Execução (Guia do Usuário)

Siga este roteiro passo a passo para testar e operar a integração completa em ambiente local:

### Passo 1: Instalação e Configurações (Apenas na primeira vez)
1. **Instalar dependências**: No terminal do seu sistema, navegue até a pasta raiz `d:\sgp-senai` e execute:
   ```bash
   pip install -r requirements.txt
   ```
2. **Definir endpoint do SGP no Coletor**: No diretório `d:\sgp-senai\collector_hipot_post`, certifique-se de que o arquivo `config.json` existe (se não existir, ele será gerado na primeira execução) e aponte para a URL do servidor local:
   ```json
   {
       "sgp_url": "http://127.0.0.1:5000"
   }
   ```

### Passo 2: Executar o Servidor Central SGP
1. No terminal do projeto, execute o script de inicialização do Flask:
   ```bash
   python main.py
   ```
2. Verifique se o log no console indica que o servidor está rodando em `http://127.0.0.1:5000`.
3. Abra o navegador web de sua preferência e acesse o endereço do Painel Live Board:
   `http://127.0.0.1:5000/producao/gp/painel/`

### Passo 3: Abrir o Coletor com Pré-preenchimento
1. No painel Kanban do SGP, localize uma ordem de produção na coluna **HI POT** (etapa B5) e clique no cartão correspondente.
2. No modal que abrir, clique no botão azul **🔌 Abrir Coletor Desktop (Hi-Pot)**.
3. Observe que o aplicativo desktop abrirá em sua tela e o campo **NÚMERO DE SÉRIE** estará preenchido de forma automática com o serial da peça selecionada.

### Passo 4: Realizar o Teste e Acompanhar a Sincronização
1. No aplicativo desktop, selecione o nome do **Operador** no campo de seleção.
2. Quando o teste elétrico físico for disparado e finalizado:
   - Os dados brutais do teste (ex: `1.25 mA`, `0.05 mR`) serão mostrados no log do coletor.
   - O teste será gravado localmente no arquivo `hipot.db`.
   - O aplicativo desktop acionará a sincronização assíncrona.
   - O indicador visual superior do coletor mostrará o status verde: `🟢 SGP Sync: Banco local totalmente sincronizado.`
3. Retorne ao navegador da Live Board do SGP. Observe que a peça testada teve a etapa B5 encerrada e avançou automaticamente para a próxima coluna do Kanban (bancada seguinte configurada no roteiro).

### Passo 5: Testar Resiliência Offline (Fila Local)
1. Pare temporariamente o servidor web Flask no terminal (pressionando `Ctrl+C`).
2. Tente abrir o modal e realizar um teste ou simplesmente simule a inserção de ensaios elétricos locais.
3. O coletor desktop salvará o teste localmente no `hipot.db` e atualizará o status de sincronização para vermelho: `🔴 SGP Sync: Servidor SGP offline (1 pendentes)`. A operação na fábrica continua sem travar a tela.
4. Reinicie o servidor Flask executando `python main.py` novamente.
5. Em até 30 segundos, o coletor desktop identificará que o servidor está online, enviará todas as pendências da fila local de forma transparente e atualizará o status de sincronização de volta para o verde (`totalmente sincronizado`), atualizando também os dados da Live Board.

---

## 7. Execução em Container Docker (Solução e Ajustes)

Se você decidir implantar a aplicação central SGP via **Docker**, a arquitetura de integração continuará sendo 100% funcional. Veja o comportamento de cada parte e como ativá-lo:

### A. Sincronização de Dados (PySide6 -> Docker)
- **Funciona perfeitamente**: Como a sincronização de banco de dados (`SyncWorker`) é baseada em chamadas HTTP REST, ela é totalmente compatível.
- A única configuração necessária é garantir que o arquivo `config.json` na estação do operador aponte para a porta pública exposta do Docker (ex: `http://localhost:5000` ou o IP do servidor na rede).

### B. Inicialização do Coletor Desktop (Board -> Windows do Operador)
- **Desafio do Container**: O container Docker roda sob um ambiente Linux isolado e sem servidor de exibição gráfica (sem GUI). Por esse motivo, o comando tradicional de servidor `subprocess.Popen` não consegue abrir janelas no Windows do operador.
- **Solução (Protocolo Customizado)**:
  Nós implementamos um mecanismo inteligente de **fallback**. Quando o servidor SGP detecta que está rodando sob Docker (ou nuvem), ele sinaliza o erro de execução local e a página web (`board.html`) abre o coletor diretamente a partir do navegador do cliente usando o protocolo customizado do Windows (`hipot://[serial]`).

### C. Passo a Passo para Ativar o Launcher no Docker:
1. No computador Windows da estação do operador, abra o terminal no diretório do projeto e execute:
   ```bash
   python collector_hipot_post/register_protocol.py
   ```
2. Este script registrará a associação do protocolo `hipot://` no Registro do Windows do usuário logado (não requer privilégios de administrador).
3. Pronto! Ao clicar no botão no SGP (rodando em Docker), o navegador chamará o Windows que abrirá a janela gráfica do coletor elétrico localmente preenchendo o número de série da peça atual.

