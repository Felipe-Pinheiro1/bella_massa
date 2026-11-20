from django.db import models


class Mesa(models.Model):
    LIVRE, OCUPADA, AGUARDANDO = 'livre', 'ocupada', 'aguardando'
    STATUS = [
        (LIVRE, 'Livre'),
        (OCUPADA, 'Ocupada'),
        (AGUARDANDO, 'Aguardando pagamento'),
    ]
    numero = models.PositiveIntegerField(unique=True)
    status = models.CharField(max_length=12, choices=STATUS, default=LIVRE)

    class Meta:
        ordering = ['numero']

    def __str__(self):
        return f'Mesa {self.numero}'

    def pedidos_em_aberto(self):
        return self.pedidos.exclude(status=Pedido.CONCLUIDO)


class Produto(models.Model):
    nome = models.CharField(max_length=80)
    descricao = models.CharField(max_length=200, blank=True)
    categoria = models.CharField(max_length=40, help_text='Ex.: pizzas, bebidas')
    preco = models.DecimalField(max_digits=7, decimal_places=2)

    class Meta:
        ordering = ['categoria', 'nome']

    def __str__(self):
        return self.nome


class Pedido(models.Model):
    PENDENTE, EM_PREPARO, CONCLUIDO = 'pendente', 'em_preparo', 'concluido'
    STATUS = [
        (PENDENTE, 'Pendente'),
        (EM_PREPARO, 'Em preparo'),
        (CONCLUIDO, 'Concluído'),
    ]
    MESA, DELIVERY = 'mesa', 'delivery'
    # mesma lista de canais do pedido de delivery (RB-003)
    CANAIS = ['iFood', 'Rappi', '99Food', 'Outro']

    tipo = models.CharField(max_length=10, default=MESA)
    mesa = models.ForeignKey(Mesa, null=True, blank=True, on_delete=models.PROTECT,
                             related_name='pedidos')
    canal = models.CharField(max_length=30, blank=True)
    cliente = models.CharField(max_length=80, blank=True)
    status = models.CharField(max_length=12, choices=STATUS, default=PENDENTE)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['criado_em']

    def __str__(self):
        return f'Pedido #{self.pk}'

    @property
    def origem(self):
        return f'Mesa {self.mesa.numero}' if self.mesa_id else f'Delivery · {self.canal}'

    @property
    def total(self):
        return sum(i.subtotal for i in self.itens.all())


class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='itens')
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT)
    quantidade = models.PositiveIntegerField(default=1)

    @property
    def subtotal(self):
        return self.produto.preco * self.quantidade
