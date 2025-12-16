from django.urls import path
from .views import * # Note : Nous importons * pour inclure toutes les vues que nous avons définies
# (login, register_client, admin_login, kyc_list, kyc_detail, etc.)
from . import views
urlpatterns = [
    # ============== API ENDPOINTS (Authentification Mobile/Flutter) ==============
    path('auth/register/client/', register_client, name='register_client'),
    path('clients/', views.list_clients, name='list_clients'),
    path('clients/<int:client_id>/update/', views.update_client, name='update_client'),
    path('clients/<int:client_id>/delete/', views.delete_client, name='delete_client'),
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
    path('artisan/conversations/<int:artisan_user_id>/', views.artisan_conversation_list, name='artisan_conversation_list'),

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

     # ================== POSTS (API) ==================
    path('posts/', post_list, name='post_list'),
    path('posts/create/', post_create, name='post_create'),
    path('posts/<int:post_id>/', post_detail, name='post_detail'),
    path('posts/<int:post_id>/delete/', post_delete, name='post_delete'),
    path('posts/<int:post_id>/like/', post_like, name='post_like'),


    # Posts
    path('posts/create/', views.post_create, name='post_create'),
    path('posts/', views.post_list, name='post_list'),
    path('posts/<int:post_id>/', views.post_detail, name='post_detail'),
    path('posts/<int:post_id>/delete/', views.post_delete, name='post_delete'),
    path('posts/<int:post_id>/like/', views.post_like, name='post_like'), # Toggle Like

    # Commentaires
    path('posts/<int:post_id>/comments/create/', views.post_comment_create, name='post_comment_create'),
    path('posts/<int:post_id>/comments/', views.post_comment_list, name='post_comment_list'),

    # Messagerie
    path('conversations/<int:user_id>/', views.conversation_list, name='conversation_list'),
    path('conversations/detail_or_create/', views.conversation_detail_or_create, name='conversation_detail_or_create'),
    path('conversations/<int:conv_id>/messages/', views.message_list, name='message_list'),
    path('conversations/<int:conv_id>/send/', views.message_send, name='message_send'),

    # Social
    path('subscriptions/toggle/', views.toggle_subscription, name='toggle_subscription'),
    path('reports/create/', views.report_create, name='report_create'),

    path('stats/dashboard/', stats_dashboard, name='stats-dashboard'),
    path('admin/stats/', admin_stats, name='admin_stats'),
    path('stats/dashboard/', stats_dashboard, name='stats-dashboard'),  # API JSON

    path('admin/clients/', views.admin_clients, name='list_clients'),
    path('admin/clients/<int:id>/update/', views.update_client, name='update_client'),
    path('admin/clients/<int:id>/delete/', views.delete_client, name='delete_client'),


]