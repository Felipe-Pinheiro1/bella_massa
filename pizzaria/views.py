from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .models import ItemPedido, Mesa, Pedido, Produto

def somente_admin(view):
    """RB-001: só o administrador (is_staff) mexe no cardápio."""
    @wraps(view)
    def interna(request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, 'Apenas o administrador acessa o cardápio.')
            return redirect('mesas')
        return view(request, *args, **kwargs)
    return interna


@login_required
def mesas(request):
    """Tela 1: painel do atendente. Lista mesas e atualiza o status (RF-006/007)."""
    if request.method == 'POST':
        mesa = get_object_or_404(Mesa, pk=request.POST.get('mesa'))
        novo = request.POST.get('status')
        if novo not in dict(Mesa.STATUS):
            messages.error(request, 'Status inválido.')
        elif novo == Mesa.LIVRE and mesa.pedidos_em_aberto().exists():
            # RB-002
            messages.error(request, f'{mesa} tem pedidos em aberto e não pode ficar livre.')
        else:
            mesa.status = novo
            mesa.save()
            messages.success(request, f'{mesa} agora está: {mesa.get_status_display()}.')
        return redirect('mesas')
    return render(request, 'mesas.html', {'mesas': Mesa.objects.all(), 'status': Mesa.STATUS})


@login_required
@somente_admin
def cardapio(request):
    """Tela 2: cadastro, edição e remoção de produtos (RF-002/011, só admin)."""
    editando = None
    if request.GET.get('editar'):
        editando = get_object_or_404(Produto, pk=request.GET['editar'])

    if request.method == 'POST':
        acao = request.POST.get('acao')
        if acao == 'remover':
            produto = get_object_or_404(Produto, pk=request.POST['id'])
            try:
                produto.delete()
                messages.success(request, 'Produto removido.')
            except Exception:
                messages.error(request, 'Produto já usado em pedidos; não pode ser removido.')
        else:
            pk = request.POST.get('id')
            produto = (Produto.objects.filter(pk=pk).first() if pk else None) or Produto()
            try:
                produto.nome = request.POST['nome'].strip()
                produto.descricao = request.POST.get('descricao', '').strip()
                produto.categoria = request.POST['categoria'].strip().lower()
                produto.preco = request.POST['preco'].replace(',', '.')
                produto.full_clean()
                produto.save()
                messages.success(request, 'Produto salvo.')
            except Exception as e:
                messages.error(request, f'Dados inválidos: {e}')
        return redirect('cardapio')
    return render(request, 'cardapio.html',
                  {'produtos': Produto.objects.all(), 'editando': editando})


@login_required
def novo_pedido(request):
    """Tela 3: registra pedido de mesa ou de delivery (RF-004/008, RB-003)."""
    produtos = Produto.objects.all()
    if request.method == 'POST':
        tipo = request.POST.get('tipo')
        itens = []
        for p in produtos:
            try:
                qtd = int(request.POST.get(f'qtd_{p.pk}') or 0)
            except ValueError:
                qtd = 0
            if qtd > 0:
                itens.append((p, qtd))

        erro = None
        mesa = None
        canal = ''
        if not itens:
            erro = 'Escolha ao menos um item.'
        elif tipo == Pedido.DELIVERY:
            canal = request.POST.get('canal', '').strip()
            if not canal:
                erro = 'Informe o canal de origem do delivery.'
        elif tipo == Pedido.MESA:
            mesa = Mesa.objects.filter(pk=request.POST.get('mesa')).first()
            if not mesa:
                erro = 'Escolha uma mesa.'
        else:
            erro = 'Escolha o tipo do pedido.'

        if erro:
            messages.error(request, erro)
            return redirect('novo_pedido')

        pedido = Pedido.objects.create(tipo=tipo, mesa=mesa, canal=canal,
                                       cliente=request.POST.get('cliente', '').strip())
        for produto, qtd in itens:
            ItemPedido.objects.create(pedido=pedido, produto=produto, quantidade=qtd)
        if mesa and mesa.status == Mesa.LIVRE:
            mesa.status = Mesa.OCUPADA
            mesa.save()
        messages.success(request, f'Pedido #{pedido.pk} enviado para a cozinha.')
        return redirect('cozinha')
    return render(request, 'novo_pedido.html',
                  {'produtos': produtos, 'mesas': Mesa.objects.all(), 'canais': Pedido.CANAIS})


@login_required
def cozinha(request):
    """Tela 4: painel da cozinha (RF-005/009)."""
    if request.method == 'POST':
        pedido = get_object_or_404(Pedido, pk=request.POST.get('pedido'))
        novo = request.POST.get('status')
        if novo in (Pedido.EM_PREPARO, Pedido.CONCLUIDO):
            pedido.status = novo
            pedido.save()
        return redirect('cozinha')
    pedidos = (Pedido.objects.exclude(status=Pedido.CONCLUIDO)
               .select_related('mesa').prefetch_related('itens__produto'))
    return render(request, 'cozinha.html', {'pedidos': pedidos})
