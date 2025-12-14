from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProduitViewSet, ArtisanViewSet
from .views import (
    homepage,  # ← IMPORT OBLIGATOIRE
    CategorieViewSet, 
    RubriqueViewSet,
    ArtisanViewSet, 
    ProduitViewSet, 
    ArtisanImageViewSet,
)

router = DefaultRouter()
router.register(r'categories', CategorieViewSet, basename='categorie')
router.register(r'rubriques', RubriqueViewSet, basename='rubrique')
router.register(r'artisans', ArtisanViewSet, basename='artisan')
router.register(r'produits', ProduitViewSet, basename='produit')
router.register(r'images', ArtisanImageViewSet, basename='image')

urlpatterns = [
    path('', homepage, name='homepage'),  # ← MAINTENANT homepage est défini
    path('', include(router.urls)),
]
