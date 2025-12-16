from django.urls import path
from .views import * # Note : Nous importons * pour inclure toutes les vues que nous avons définies
# (login, register_client, admin_login, kyc_list, kyc_detail, etc.)

urlpatterns = [
    # ============== API ENDPOINTS (Authentification Mobile/Flutter) ==============
    path('auth/register/client/', register_client, name='register_client'),
    path('auth/register/artisan/', register_artisan, name='register_artisan'),
    path('auth/login/', login, name='login'), # API Login (Retourne JSON, y compris is_admin)

    # ================== ACTIVITE (API) ==================
    path('activites/', activite_list, name='activite_list'),
    path('activites/create/', activite_create, name='activite_create'),
    path('activites/update/<int:activite_id>/', activite_update, name='activite_update'),
    path('activites/delete/<int:activite_id>/', activite_delete, name='activite_delete'),

    # ================== SPECIALITE (API) ==================
    path('specialites/', specialite_list, name='specialite_list'),
    path('specialites/create/', specialite_create, name='specialite_create'),
    path('specialites/update/<int:specialite_id>/', specialite_update, name='specialite_update'),
    path('specialites/delete/<int:specialite_id>/', specialite_delete, name='specialite_delete'),

    # ================== ARTISAN (API) ==================
    path('artisan/', artisan_list, name='artisan_list'),
    path('artisan/create/', artisan_create, name='artisan_create'),
    path('artisan/update/<int:artisan_id>/', artisan_update, name='artisan_update'),
    path('artisan/delete/<int:artisan_id>/', artisan_delete, name='artisan_delete'),

    # ================== ARTISAN KYC (API) ==================
    path('artisan/kyc/submit/', artisan_kyc_submit, name='artisan_kyc_submit'), 
    
    
    # ============== ADMIN DASHBOARD (Web HTML Vues) ==============
    
    # Authentification Admin
    path('admin/login/', admin_login, name='admin_login'), 
    path('admin/logout/', admin_logout, name='admin_logout'), 
    
    # Tableau de Bord
    path('admin/dashboard/', admin_dashboard, name='admin_dashboard'), 

    # Gestion KYC
    path('admin/kyc/list/', kyc_list, name='kyc_list'), # Liste des KYC en attente/à revoir
    path('admin/kyc/detail/<int:kyc_id>/', kyc_detail, name='kyc_detail'), # Vue des documents
    
    # Actions de validation (POST)
    path('admin/kyc/validate/<int:kyc_id>/', kyc_validate, name='kyc_validate'),
    path('admin/kyc/reject/<int:kyc_id>/', kyc_reject, name='kyc_reject'),
]