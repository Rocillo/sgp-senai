from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.models_sqla import (
    CompraRequisicao,
    CompraRequisicaoItem,
    CompraHistoricoStatus,
    Peca,
)

requisicoes_bp = Blueprint("requisicoes", __name__, url_prefix="/compras/requisicoes")


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] _gerar_numero_requisicao
# [RESPONSABILIDADE] Gerar número sequencial de requisição baseado no tipo (PRODUTIVO/NAO_PRODUTIVO)
# ====================================================================
def _gerar_numero_requisicao(tipo_requisicao):
    """
    Gera número automático de requisição no formato:
    - RC-PRO-000001 para tipo PRODUTIVO
    - RC-NPR-000001 para tipo NAO_PRODUTIVO

    A sequência é independente por tipo.
    """
    if tipo_requisicao == "PRODUTIVO":
        prefixo = "RC-PRO-"
    else:
        prefixo = "RC-NPR-"

    # Buscar última requisição do mesmo tipo
    ultima = (
        CompraRequisicao.query.filter(
            CompraRequisicao.numero_requisicao.like(f"{prefixo}%")
        )
        .order_by(CompraRequisicao.id.desc())
        .first()
    )

    if ultima:
        # Extrair número da última requisição e incrementar
        try:
            ultimo_numero = int(ultima.numero_requisicao.split("-")[-1])
            proximo_numero = ultimo_numero + 1
        except (ValueError, IndexError):
            proximo_numero = 1
    else:
        proximo_numero = 1

    return f"{prefixo}{proximo_numero:06d}"


# ====================================================================
# [FIM BLOCO] _gerar_numero_requisicao
# ====================================================================


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] _alterar_status_requisicao
# [RESPONSABILIDADE] Alterar status de requisição e registrar no histórico
# ====================================================================
def _alterar_status_requisicao(id, novo_status, comentario):
    """
    Função central para alterar status de requisição.

    Args:
        id: ID da requisição
        novo_status: Novo status (APROVADA, REJEITADA, COMPRADA, ENTREGUE)
        comentario: Comentário sobre a mudança

    Returns:
        tuple: (sucesso: bool, mensagem: str)
    """
    try:
        # Buscar requisição
        requisicao = CompraRequisicao.query.get(id)
        if not requisicao:
            return False, "Requisição não encontrada"

        # Guardar status anterior
        status_anterior = requisicao.status

        # Atualizar requisição
        requisicao.status = novo_status
        requisicao.atualizado_em = datetime.utcnow()

        # Criar registro no histórico
        historico = CompraHistoricoStatus(
            requisicao_id=requisicao.id,
            status_anterior=status_anterior,
            status_novo=novo_status,
            usuario_id=current_user.id if current_user.is_authenticated else None,
            usuario_nome_snapshot=(
                current_user.username if current_user.is_authenticated else None
            ),
            data_evento=datetime.utcnow(),
            comentario=comentario,
            origem_evento="usuario",
        )

        db.session.add(historico)
        db.session.commit()

        return True, f"Status alterado para {novo_status}"

    except Exception as e:
        db.session.rollback()
        return False, f"Erro ao alterar status: {str(e)}"


# ====================================================================
# [FIM BLOCO] _alterar_status_requisicao
# ====================================================================


@requisicoes_bp.route("/", methods=["GET"])
@login_required
def listar_requisicoes():
    """Lista todas as requisições de compras com filtros"""
    # Obter parâmetros de filtro
    filtro_status = request.args.get("status", "")
    filtro_tipo = request.args.get("tipo", "")
    filtro_solicitante = request.args.get("solicitante", "")
    filtro_setor = request.args.get("setor", "")
    filtro_data = request.args.get("data", "")
    busca = request.args.get("busca", "").strip()

    # Query base
    query = CompraRequisicao.query.filter_by(ativo=True)

    # Aplicar filtros
    if filtro_status:
        query = query.filter(CompraRequisicao.status == filtro_status)

    if filtro_tipo:
        if filtro_tipo == "PRODUTIVO":
            query = query.filter(CompraRequisicao.numero_requisicao.like("%-PRO-%"))
        elif filtro_tipo == "NAO_PRODUTIVO":
            query = query.filter(CompraRequisicao.numero_requisicao.like("%-NPR-%"))

    if filtro_solicitante:
        query = query.filter(
            CompraRequisicao.solicitante_nome_snapshot == filtro_solicitante
        )

    if filtro_setor:
        query = query.filter(CompraRequisicao.setor == filtro_setor)

    if filtro_data:
        try:
            data_filtro = datetime.strptime(filtro_data, "%Y-%m-%d").date()
            query = query.filter(
                db.func.date(CompraRequisicao.data_solicitacao) == data_filtro
            )
        except ValueError:
            pass

    # Aplicar busca textual
    if busca:
        query = query.filter(
            db.or_(
                CompraRequisicao.numero_requisicao.ilike(f"%{busca}%"),
                CompraRequisicao.solicitante_nome_snapshot.ilike(f"%{busca}%"),
                CompraRequisicao.setor.ilike(f"%{busca}%"),
            )
        )

    # Ordenar e executar
    requisicoes = query.order_by(CompraRequisicao.data_solicitacao.desc()).all()

    # Buscar opções distintas para os filtros
    status_options = ["SOLICITADA", "APROVADA", "REJEITADA", "COMPRADA", "ENTREGUE"]
    tipo_options = ["PRODUTIVO", "NAO_PRODUTIVO"]

    solicitante_options = (
        db.session.query(CompraRequisicao.solicitante_nome_snapshot)
        .filter(CompraRequisicao.solicitante_nome_snapshot.isnot(None))
        .filter(CompraRequisicao.ativo == True)
        .distinct()
        .order_by(CompraRequisicao.solicitante_nome_snapshot)
        .all()
    )
    solicitante_options = [s[0] for s in solicitante_options if s[0]]

    setor_options = (
        db.session.query(CompraRequisicao.setor)
        .filter(CompraRequisicao.setor.isnot(None))
        .filter(CompraRequisicao.ativo == True)
        .distinct()
        .order_by(CompraRequisicao.setor)
        .all()
    )
    setor_options = [s[0] for s in setor_options if s[0]]

    return render_template(
        "compras_templates/requisicoes/listar_requisicoes.html",
        requisicoes=requisicoes,
        status_options=status_options,
        tipo_options=tipo_options,
        solicitante_options=solicitante_options,
        setor_options=setor_options,
        filtro_status=filtro_status,
        filtro_tipo=filtro_tipo,
        filtro_solicitante=filtro_solicitante,
        filtro_setor=filtro_setor,
        filtro_data=filtro_data,
        busca=busca,
    )


@requisicoes_bp.route("/nova", methods=["GET", "POST"])
@login_required
def nova_requisicao():
    """Formulário para criar nova requisição"""
    if request.method == "POST":
        try:
            # Coletar dados do formulário
            tipo_requisicao = request.form.get("tipo_requisicao")
            setor = request.form.get("setor")
            urgencia = request.form.get("urgencia")
            prazo_desejado_str = request.form.get("prazo_desejado")
            observacao_geral = request.form.get("observacao_geral", "").strip()

            # Dados do item
            peca_id = request.form.get("peca_id")
            codigo_pneumark = request.form.get("codigo_pneumark")
            descricao = request.form.get("descricao")
            quantidade = request.form.get("quantidade")
            link_referencia = request.form.get("link_referencia")

            # Dados do parecer
            parecer_status = request.form.get("parecer_status")
            parecer_nivel = request.form.get("parecer_nivel")
            parecer_mensagem = request.form.get("parecer_mensagem")
            parecer_quantidade_sugerida = request.form.get(
                "parecer_quantidade_sugerida"
            )
            parecer_excesso_atual = request.form.get("parecer_excesso_atual")

            # Validação obrigatória: requisição produtiva DEVE ter peca_id
            if tipo_requisicao == "PRODUTIVO":
                if not peca_id:
                    flash(
                        "Selecione uma peça válida do estoque antes de enviar a requisição produtiva.",
                        "error",
                    )
                    return render_template(
                        "compras_templates/requisicoes/nova_requisicao.html"
                    )

                # Buscar peça real do banco e forçar recálculo
                try:
                    peca = Peca.query.get(int(peca_id))
                    if not peca:
                        flash("Peça não encontrada no estoque.", "error")
                        return render_template(
                            "compras_templates/requisicoes/nova_requisicao.html"
                        )

                    # Forçar uso dos dados reais da peça (não confiar no formulário)
                    codigo_pneumark = peca.codigo_pneumark
                    descricao = peca.descricao

                    # Recalcular análise obrigatoriamente com dados reais
                    if (
                        peca.ponto_pedido is not None
                        and peca.estoque_maximo is not None
                    ):
                        estoque_atual = (
                            float(peca.estoque_atual) if peca.estoque_atual else 0
                        )
                        estoque_maximo = float(peca.estoque_maximo)
                        quantidade_float = float(quantidade)
                        estoque_projetado = estoque_atual + quantidade_float

                        # Recalcular parecer baseado em estoque projetado
                        if estoque_projetado > estoque_maximo:
                            parecer_status = "NAO_RECOMENDADA"
                            parecer_nivel = "vermelho"
                            parecer_mensagem = "Compra não recomendada. A quantidade solicitada ultrapassa o estoque máximo."
                            parecer_quantidade_sugerida = "0"
                            parecer_excesso_atual = str(
                                int(estoque_projetado - estoque_maximo)
                            )

                except ValueError:
                    flash("ID de peça inválido.", "error")
                    return render_template(
                        "compras_templates/requisicoes/nova_requisicao.html"
                    )

            # Validação backend: se produtivo e não recomendada, exigir justificativa
            if tipo_requisicao == "PRODUTIVO" and parecer_status == "NAO_RECOMENDADA":
                if not observacao_geral:
                    flash(
                        "Justificativa obrigatória para compra contra recomendação do sistema.",
                        "error",
                    )
                    return render_template(
                        "compras_templates/requisicoes/nova_requisicao.html"
                    )

            # Converter prazo desejado para date se fornecido
            prazo_desejado = None
            if prazo_desejado_str:
                try:
                    prazo_desejado = datetime.strptime(
                        prazo_desejado_str, "%Y-%m-%d"
                    ).date()
                except ValueError:
                    pass

            # Gerar número da requisição
            numero_requisicao = _gerar_numero_requisicao(tipo_requisicao)

            # Criar requisição
            requisicao = CompraRequisicao(
                numero_requisicao=numero_requisicao,
                solicitante_id=(
                    current_user.id if current_user.is_authenticated else None
                ),
                solicitante_nome_snapshot=(
                    current_user.username if current_user.is_authenticated else None
                ),
                setor=setor,
                status="SOLICITADA",
                urgencia=urgencia,
                prazo_desejado=prazo_desejado,
                data_solicitacao=datetime.utcnow(),
                observacao_geral=observacao_geral,
                ativo=True,
                criado_em=datetime.utcnow(),
            )

            db.session.add(requisicao)
            db.session.flush()  # Para obter o ID da requisição

            # Determinar se é decisão contra recomendação
            decisao_contra_recomendacao = (
                tipo_requisicao == "PRODUTIVO" and parecer_status == "NAO_RECOMENDADA"
            )

            # Criar item da requisição
            # Para PRODUTIVO, usar dados reais da peça; para NAO_PRODUTIVO, usar dados digitados
            if tipo_requisicao == "PRODUTIVO" and peca_id:
                # Buscar peça novamente para garantir dados corretos
                peca_real = Peca.query.get(int(peca_id))
                item = CompraRequisicaoItem(
                    requisicao_id=requisicao.id,
                    tipo_item=tipo_requisicao,
                    peca_id=int(peca_id),
                    codigo_pneumark_snapshot=(
                        peca_real.codigo_pneumark if peca_real else None
                    ),
                    descricao_snapshot=peca_real.descricao if peca_real else None,
                    descricao_digitada=None,  # Não usar descrição digitada para produtivo
                    quantidade=float(quantidade),
                    unidade=None,
                    estoque_atual_snapshot=(
                        float(peca_real.estoque_atual)
                        if peca_real and peca_real.estoque_atual
                        else None
                    ),
                    ultimo_preco_referencia=None,
                    link_referencia_principal=(
                        link_referencia if link_referencia else None
                    ),
                    observacao_item=None,
                    # Dados do parecer
                    parecer_status=parecer_status if parecer_status else None,
                    parecer_nivel=parecer_nivel if parecer_nivel else None,
                    parecer_mensagem=parecer_mensagem if parecer_mensagem else None,
                    parecer_quantidade_sugerida=(
                        int(parecer_quantidade_sugerida)
                        if parecer_quantidade_sugerida
                        else None
                    ),
                    parecer_excesso_atual=(
                        int(parecer_excesso_atual) if parecer_excesso_atual else None
                    ),
                    decisao_contra_recomendacao=decisao_contra_recomendacao,
                    ativo=True,
                    criado_em=datetime.utcnow(),
                )
            else:
                # Não produtivo - usar dados digitados
                item = CompraRequisicaoItem(
                    requisicao_id=requisicao.id,
                    tipo_item=tipo_requisicao,
                    peca_id=None,
                    codigo_pneumark_snapshot=(
                        codigo_pneumark if codigo_pneumark else None
                    ),
                    descricao_snapshot=None,
                    descricao_digitada=descricao,
                    quantidade=float(quantidade),
                    unidade=None,
                    estoque_atual_snapshot=None,
                    ultimo_preco_referencia=None,
                    link_referencia_principal=(
                        link_referencia if link_referencia else None
                    ),
                    observacao_item=None,
                    # Dados do parecer
                    parecer_status=parecer_status if parecer_status else None,
                    parecer_nivel=parecer_nivel if parecer_nivel else None,
                    parecer_mensagem=parecer_mensagem if parecer_mensagem else None,
                    parecer_quantidade_sugerida=(
                        int(parecer_quantidade_sugerida)
                        if parecer_quantidade_sugerida
                        else None
                    ),
                    parecer_excesso_atual=(
                        int(parecer_excesso_atual) if parecer_excesso_atual else None
                    ),
                    decisao_contra_recomendacao=decisao_contra_recomendacao,
                    ativo=True,
                    criado_em=datetime.utcnow(),
                )

            db.session.add(item)

            # Criar histórico de status inicial com comentário apropriado
            if decisao_contra_recomendacao:
                comentario_historico = (
                    f"Requisição criada contra recomendação do sistema. "
                    f"Parecer: {parecer_mensagem}. "
                    f"Justificativa: {observacao_geral}"
                )
            else:
                comentario_historico = "Requisição criada"

            historico = CompraHistoricoStatus(
                requisicao_id=requisicao.id,
                status_anterior=None,
                status_novo="SOLICITADA",
                usuario_id=current_user.id if current_user.is_authenticated else None,
                usuario_nome_snapshot=(
                    current_user.username if current_user.is_authenticated else None
                ),
                data_evento=datetime.utcnow(),
                comentario=comentario_historico,
                origem_evento="sistema",
            )

            db.session.add(historico)
            db.session.commit()

            flash(f"Requisição {numero_requisicao} criada com sucesso!", "success")
            return redirect(url_for("requisicoes.listar_requisicoes"))

        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao criar requisição: {str(e)}", "error")
            return render_template("compras_templates/requisicoes/nova_requisicao.html")

    return render_template("compras_templates/requisicoes/nova_requisicao.html")


@requisicoes_bp.route("/<int:id>", methods=["GET"])
@login_required
def detalhe_requisicao(id):
    """Exibe detalhes de uma requisição específica"""
    requisicao = CompraRequisicao.query.get_or_404(id)
    itens = CompraRequisicaoItem.query.filter_by(requisicao_id=id, ativo=True).all()
    historico = (
        CompraHistoricoStatus.query.filter_by(requisicao_id=id)
        .order_by(CompraHistoricoStatus.data_evento.asc())
        .all()
    )

    # Criar resumo do fluxo baseado no histórico
    resumo_fluxo = {
        "SOLICITADA": None,
        "APROVADA": None,
        "COMPRADA": None,
        "ENTREGUE": None,
        "REJEITADA": None,
    }

    # Preencher com a primeira ocorrência de cada status
    for item in historico:
        if item.status_novo in resumo_fluxo and resumo_fluxo[item.status_novo] is None:
            resumo_fluxo[item.status_novo] = item.data_evento

    return render_template(
        "compras_templates/requisicoes/detalhe_requisicao.html",
        requisicao=requisicao,
        itens=itens,
        historico=historico,
        resumo_fluxo=resumo_fluxo,
    )


@requisicoes_bp.route("/<int:id>/aprovar", methods=["POST"])
@login_required
def aprovar_requisicao(id):
    """Aprovar uma requisição"""
    sucesso, mensagem = _alterar_status_requisicao(
        id=id, novo_status="APROVADA", comentario="Requisição aprovada"
    )

    if sucesso:
        flash(mensagem, "success")
    else:
        flash(mensagem, "error")

    return redirect(url_for("requisicoes.detalhe_requisicao", id=id))


@requisicoes_bp.route("/<int:id>/rejeitar", methods=["POST"])
@login_required
def rejeitar_requisicao(id):
    """Rejeitar uma requisição"""
    sucesso, mensagem = _alterar_status_requisicao(
        id=id, novo_status="REJEITADA", comentario="Requisição rejeitada"
    )

    if sucesso:
        flash(mensagem, "success")
    else:
        flash(mensagem, "error")

    return redirect(url_for("requisicoes.detalhe_requisicao", id=id))


@requisicoes_bp.route("/<int:id>/marcar-comprada", methods=["POST"])
@login_required
def marcar_comprada(id):
    """Marcar requisição como comprada"""
    sucesso, mensagem = _alterar_status_requisicao(
        id=id, novo_status="COMPRADA", comentario="Compra realizada"
    )

    if sucesso:
        flash(mensagem, "success")
    else:
        flash(mensagem, "error")

    return redirect(url_for("requisicoes.detalhe_requisicao", id=id))


@requisicoes_bp.route("/<int:id>/entregar", methods=["POST"])
@login_required
def entregar_requisicao(id):
    """Marcar requisição como entregue"""
    sucesso, mensagem = _alterar_status_requisicao(
        id=id, novo_status="ENTREGUE", comentario="Entregue ao solicitante"
    )

    if sucesso:
        flash(mensagem, "success")
    else:
        flash(mensagem, "error")

    return redirect(url_for("requisicoes.detalhe_requisicao", id=id))


@requisicoes_bp.route("/api/pecas", methods=["GET"])
@login_required
def api_buscar_pecas():
    """API para buscar peças do estoque"""
    q = request.args.get("q", "").strip()

    if not q or len(q) < 2:
        return jsonify([])

    # Buscar por código ou descrição
    pecas = (
        Peca.query.filter(
            db.or_(Peca.codigo_pneumark.ilike(f"%{q}%"), Peca.descricao.ilike(f"%{q}%"))
        )
        .limit(20)
        .all()
    )

    # Serializar resultados
    resultados = []
    for peca in pecas:
        resultados.append(
            {
                "id": peca.id,
                "codigo_pneumark": peca.codigo_pneumark,
                "descricao": peca.descricao,
                "estoque_atual": float(peca.estoque_atual) if peca.estoque_atual else 0,
                "ponto_pedido": float(peca.ponto_pedido) if peca.ponto_pedido else None,
                "estoque_maximo": (
                    float(peca.estoque_maximo) if peca.estoque_maximo else None
                ),
                "custo": float(peca.custo) if peca.custo else None,
            }
        )

    return jsonify(resultados)


@requisicoes_bp.route("/api/pecas/<int:peca_id>/analise", methods=["GET"])
@login_required
def api_analise_peca(peca_id):
    """API para análise de compra de uma peça"""
    peca = Peca.query.get_or_404(peca_id)

    # Obter quantidade solicitada (opcional)
    quantidade_str = request.args.get("quantidade", "")
    quantidade_solicitada = 0
    if quantidade_str:
        try:
            quantidade_solicitada = float(quantidade_str)
        except ValueError:
            quantidade_solicitada = 0

    # Dados básicos
    analise = {
        "peca_id": peca.id,
        "codigo_pneumark": peca.codigo_pneumark,
        "descricao": peca.descricao,
        "estoque_atual": float(peca.estoque_atual) if peca.estoque_atual else 0,
        "ponto_pedido": float(peca.ponto_pedido) if peca.ponto_pedido else None,
        "estoque_maximo": float(peca.estoque_maximo) if peca.estoque_maximo else None,
        "custo": float(peca.custo) if peca.custo else None,
    }

    # Verificar se dados estão completos
    if peca.ponto_pedido is None or peca.estoque_maximo is None:
        analise.update(
            {
                "status": "DADOS_INCOMPLETOS",
                "nivel": "cinza",
                "mensagem": "Cadastro incompleto. Ponto de pedido ou estoque máximo não definidos.",
                "quantidade_sugerida": 0,
            }
        )
        return jsonify(analise)

    estoque_atual = float(peca.estoque_atual) if peca.estoque_atual else 0
    ponto_pedido = float(peca.ponto_pedido)
    estoque_maximo = float(peca.estoque_maximo)

    # Calcular estoque projetado se quantidade foi informada
    estoque_projetado = (
        estoque_atual + quantidade_solicitada
        if quantidade_solicitada > 0
        else estoque_atual
    )

    # Calcular quantidade sugerida (sempre estoque_maximo - estoque_atual)
    quantidade_sugerida = (
        int(estoque_maximo - estoque_atual) if estoque_atual < estoque_maximo else 0
    )

    # Se quantidade foi informada e ultrapassa estoque máximo
    if quantidade_solicitada > 0 and estoque_projetado > estoque_maximo:
        excesso_projetado = int(estoque_projetado - estoque_maximo)
        analise.update(
            {
                "status": "NAO_RECOMENDADA",
                "nivel": "vermelho",
                "mensagem": "Compra não recomendada. A quantidade solicitada ultrapassa o estoque máximo.",
                "quantidade_sugerida": quantidade_sugerida,
                "excesso_atual": excesso_projetado,
                "estoque_projetado": int(estoque_projetado),
                "excesso_projetado": excesso_projetado,
            }
        )
        return jsonify(analise)

    # Regras de análise baseadas no estoque atual (sem quantidade ou quantidade não ultrapassa)
    if estoque_atual <= ponto_pedido:
        analise.update(
            {
                "status": "RECOMENDADA",
                "nivel": "verde",
                "mensagem": "Compra recomendada. Estoque atual está no ponto de pedido ou abaixo.",
                "quantidade_sugerida": int(estoque_maximo - estoque_atual),
            }
        )
    elif estoque_atual < estoque_maximo:
        analise.update(
            {
                "status": "ATENCAO",
                "nivel": "amarelo",
                "mensagem": "Compra permitida com atenção. Estoque atual ainda está acima do ponto de pedido.",
                "quantidade_sugerida": int(estoque_maximo - estoque_atual),
            }
        )
    else:  # estoque_atual >= estoque_maximo
        analise.update(
            {
                "status": "NAO_RECOMENDADA",
                "nivel": "vermelho",
                "mensagem": "Compra não recomendada. Estoque atual está acima do estoque máximo.",
                "quantidade_sugerida": 0,
                "excesso_atual": int(estoque_atual - estoque_maximo),
            }
        )

    return jsonify(analise)


# ====================================================================
# MAPA DO ARQUIVO
# --------------------------------------------------------------------
# FUNÇÃO: _gerar_numero_requisicao
# FUNÇÃO: _alterar_status_requisicao
# ROTA: listar_requisicoes (GET)
# ROTA: nova_requisicao (GET, POST)
# ROTA: detalhe_requisicao (GET)
# ROTA: aprovar_requisicao (POST)
# ROTA: rejeitar_requisicao (POST)
# ROTA: marcar_comprada (POST)
# ROTA: entregar_requisicao (POST)
# ROTA API: api_buscar_pecas (GET)
# ROTA API: api_analise_peca (GET)
# ====================================================================
