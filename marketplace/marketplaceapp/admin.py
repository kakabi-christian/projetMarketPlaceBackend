from django.contrib import admin
from .models import (
    Categorie, Rubrique, Artisan, Produit, 
    ArtisanImage, StatistiqueArtisan
)

@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ['nom_categorie', 'actif', 'ordre']
    list_filter = ['actif']
    search_fields = ['nom_categorie']

@admin.register(Rubrique)
class RubriqueAdmin(admin.ModelAdmin):
    list_display = ['nom_rubrique', 'categorie', 'actif']
    list_filter = ['categorie', 'actif']
    search_fields = ['nom_rubrique']

@admin.register(Artisan)
class ArtisanAdmin(admin.ModelAdmin):
    list_display = ['nom_entreprise', 'categorie', 'ville', 'actif', 'date_creation']
    list_filter = ['categorie', 'rubrique', 'actif', 'pays']
    search_fields = ['nom_entreprise', 'nom_proprietaire', 'ville']
    readonly_fields = ['date_creation', 'slug']

# ✅ CORRIGÉ
@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    list_display = ['nom', 'artisan', 'prix', 'disponible', 'date_creation']
    list_filter = ['artisan', 'disponible', 'date_creation']  # ✅ Champs existants
    search_fields = ['nom', 'description']
    list_per_page = 20

