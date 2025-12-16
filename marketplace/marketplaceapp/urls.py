from django.urls import path
from .views import register_client, login
from .views import *

urlpatterns = [
    # Authentification client
    path('auth/register/client/', register_client, name='register_client'),
    path('auth/register/artisan/', register_artisan, name='register_artisan'),
    path('auth/login/', login, name='login'),

    # ================== ACTIVITE ==================
    path('activites/', activite_list, name='activite_list'),
    path('activites/create/', activite_create, name='activite_create'),
    path('activites/update/<int:activite_id>/', activite_update, name='activite_update'),
    path('activites/delete/<int:activite_id>/', activite_delete, name='activite_delete'),

    # ================== SPECIALITE ==================
    path('specialites/', specialite_list, name='specialite_list'),
    path('specialites/create/', specialite_create, name='specialite_create'),
    path('specialites/update/<int:specialite_id>/', specialite_update, name='specialite_update'),
    path('specialites/delete/<int:specialite_id>/', specialite_delete, name='specialite_delete'),

    # ================== ARTISAN ==================
    path('artisan/', artisan_list, name='artisan_list'),
    path('artisan/create/', artisan_create, name='artisan_create'),
    path('artisan/update/<int:artisan_id>/', artisan_update, name='artisan_update'),
    path('artisan/delete/<int:artisan_id>/', artisan_delete, name='artisan_delete'),

    # ================== ARTISAN KYC (NOUVELLE ROUTE) ==================
    path('artisan/kyc/submit/', artisan_kyc_submit, name='artisan_kyc_submit'), # <-- AJOUT ICI
]
