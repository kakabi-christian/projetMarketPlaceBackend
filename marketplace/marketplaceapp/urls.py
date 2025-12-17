# marketplaceapp/urls.py - VERSION COMPLÈTE ET CORRIGÉE

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    # Pages
    homepage,
    
    # ViewSets
    CategorieViewSet,
    RubriqueViewSet,
    ArtisanViewSet,
    ProduitViewSet,
    ArtisanImageViewSet,
    ProfilClientViewSet,
    
    # Auth
    RegisterView,
    LoginView,
    LogoutView,
    MeView,
    ChangePasswordView,
    UpdateProfileView,
    
    # Admin
    AdminStatsView,
    AdminUsersView,
    AdminUserDetailView,
    AdminUserToggleActiveView,
    
    # ✅ CHAT - Nouvelles classes
    ConversationViewSet,
    ArtisanConversationsView,
    ArtisanConversationDetailView,
)

# ============================================================================
# ROUTER pour les ViewSets
# ============================================================================

router = DefaultRouter()
router.register(r'categories', CategorieViewSet, basename='categorie')
router.register(r'rubriques', RubriqueViewSet, basename='rubrique')
router.register(r'artisans', ArtisanViewSet, basename='artisan')
router.register(r'produits', ProduitViewSet, basename='produit')
router.register(r'artisan-images', ArtisanImageViewSet, basename='artisan-image')
router.register(r'profils-clients', ProfilClientViewSet, basename='profil-client')

# ✅ CHAT ViewSet
router.register(r'chat/conversations', ConversationViewSet, basename='conversation')

# ============================================================================
# URL PATTERNS
# ============================================================================

urlpatterns = [
    # Router (inclut tous les ViewSets)
    path('', include(router.urls)),
    
    # ============================================================================
    # HOMEPAGE
    # ============================================================================
    path('', homepage, name='homepage'),
    
    # ============================================================================
    # AUTH
    # ============================================================================
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/me/', MeView.as_view(), name='me'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('auth/profile/', UpdateProfileView.as_view(), name='update-profile'),
    
    # ============================================================================
    # ADMIN
    # ============================================================================
    path('admin/stats/', AdminStatsView.as_view(), name='admin-stats'),
    path('admin/users/', AdminUsersView.as_view(), name='admin-users-list'),
    path('admin/users/<int:user_id>/', AdminUserDetailView.as_view(), name='admin-user-detail'),
    path('admin/users/<int:user_id>/toggle-active/', AdminUserToggleActiveView.as_view(), name='admin-user-toggle'),
    
    # ============================================================================
    # ✅ CHAT - Routes spécifiques pour l'artisan
    # ============================================================================
    path('chat/artisan/conversations/', ArtisanConversationsView.as_view(), name='artisan-conversations-list'),
    path('chat/artisan/conversations/<int:conversation_id>/', ArtisanConversationDetailView.as_view(), name='artisan-conversation-detail'),
]