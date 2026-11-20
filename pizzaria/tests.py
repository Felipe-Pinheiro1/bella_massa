from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Mesa, Pedido, Produto


class FluxoTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user('adm', password='x', is_staff=True)
        self.atend = User.objects.create_user('at', password='x')
        self.mesa = Mesa.objects.create(numero=1)
        self.produto = Produto.objects.create(nome='Brotinho', categoria='pizzas',
                                              preco=Decimal('17.99'))

    def test_telas_exigem_login(self):
        for nome in ('mesas', 'novo_pedido', 'cozinha', 'cardapio'):
            r = self.client.get(reverse(nome))
            self.assertRedirects(r, f"{reverse('login')}?next={reverse(nome)}")

    def test_login(self):
        r = self.client.post(reverse('login'), {'username': 'at', 'password': 'x'})
        self.assertRedirects(r, reverse('mesas'))

    def test_cardapio_so_admin(self):  # RB-001
        self.client.force_login(self.atend)
        self.assertRedirects(self.client.get(reverse('cardapio')), reverse('mesas'),
                             fetch_redirect_response=False)
        self.client.force_login(self.admin)
        self.client.post(reverse('cardapio'),
                         {'nome': 'Média', 'categoria': 'Pizzas', 'preco': '39,99'})
        self.assertEqual(str(Produto.objects.get(nome='Média').preco), '39.99')

    def test_cardapio_cria_produto_com_id_vazio(self):
        # o formulario real envia o campo oculto "id" vazio ao criar
        self.client.force_login(self.admin)
        r = self.client.post(reverse('cardapio'), {
            'id': '', 'nome': 'Família', 'categoria': 'Pizzas', 'preco': '59,99'})
        self.assertRedirects(r, reverse('cardapio'))
        self.assertEqual(str(Produto.objects.get(nome='Família').preco), '59.99')

    def test_pedido_mesa_vai_para_cozinha_e_bloqueia_livre(self):  # RF-004, RB-002
        self.client.force_login(self.atend)
        self.client.post(reverse('novo_pedido'), {
            'tipo': 'mesa', 'mesa': self.mesa.pk, f'qtd_{self.produto.pk}': '2'})
        pedido = Pedido.objects.get()
        self.assertEqual(pedido.total, 2 * self.produto.preco)
        self.mesa.refresh_from_db()
        self.assertEqual(self.mesa.status, Mesa.OCUPADA)
        self.assertContains(self.client.get(reverse('cozinha')), 'Mesa 1')

        self.client.post(reverse('mesas'), {'mesa': self.mesa.pk, 'status': 'livre'})
        self.mesa.refresh_from_db()
        self.assertEqual(self.mesa.status, Mesa.OCUPADA)  # bloqueado

        self.client.post(reverse('cozinha'), {'pedido': pedido.pk, 'status': 'concluido'})
        self.client.post(reverse('mesas'), {'mesa': self.mesa.pk, 'status': 'livre'})
        self.mesa.refresh_from_db()
        self.assertEqual(self.mesa.status, Mesa.LIVRE)

    def test_delivery_exige_canal(self):  # RB-003
        self.client.force_login(self.atend)
        dados = {'tipo': 'delivery', f'qtd_{self.produto.pk}': '1'}
        self.client.post(reverse('novo_pedido'), {**dados, 'canal': ''})
        self.assertEqual(Pedido.objects.count(), 0)
        self.client.post(reverse('novo_pedido'), {**dados, 'canal': 'iFood'})
        self.assertEqual(Pedido.objects.get().origem, 'Delivery · iFood')
