from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from pizzaria.models import Mesa, Produto

PRODUTOS = [
    ('Brotinho', 'Pizza de 4 fatias, 18cm', 'pizzas', '17.99'),
    ('Pequena', 'Pizza de 6 fatias, 24cm', 'pizzas', '29.99'),
    ('Média', 'Pizza de 8 fatias, 30cm', 'pizzas', '39.99'),
    ('Grande', 'Pizza de 10 fatias, 36cm', 'pizzas', '49.99'),
    ('Coca-Cola', 'Lata 350ml', 'bebidas', '6.99'),
    ('Coca-Cola 1L', 'Garrafa 1 litro', 'bebidas', '16.99'),
    ('Cerveja', 'Long neck', 'bebidas', '19.99'),
]


class Command(BaseCommand):
    help = 'Cria dados de exemplo (mesas, produtos e usuários de desenvolvimento).'

    def handle(self, *args, **opts):
        for n in range(1, 8):
            Mesa.objects.get_or_create(numero=n)
        for nome, desc, cat, preco in PRODUTOS:
            Produto.objects.get_or_create(
                nome=nome, defaults={'descricao': desc, 'categoria': cat, 'preco': preco})
        if not User.objects.filter(username='admin').exists():
            User.objects.create_user('admin', password='admin123', is_staff=True)
        if not User.objects.filter(username='atendente').exists():
            User.objects.create_user('atendente', password='atendente123')
        self.stdout.write(self.style.SUCCESS('Dados de exemplo criados.'))
