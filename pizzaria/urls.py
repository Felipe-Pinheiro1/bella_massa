from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path('', views.mesas, name='mesas'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('sair/', auth_views.LogoutView.as_view(), name='logout'),
    path('cardapio/', views.cardapio, name='cardapio'),
    path('pedido/novo/', views.novo_pedido, name='novo_pedido'),
    path('cozinha/', views.cozinha, name='cozinha'),
]
