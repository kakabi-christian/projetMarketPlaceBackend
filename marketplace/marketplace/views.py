# views.py - IMPORTS CORRIGÉS (remplacer les lignes 1-30)

from django.shortcuts import render
from django.contrib.auth.models import User
from django.contrib.auth import update_session_auth_hash

from rest_framework import viewsets, generics, status, permissions, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView

from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    Categorie, Rubrique, Artisan,
    Produit, ArtisanImage, StatistiqueArtisan, 
    ImageProduit, UserProfile
)

from .serializers import (
    CategorieSerializer, RubriqueSerializer,
    ArtisanListSerializer, ArtisanDetailSerializer,
    ArtisanCreateUpdateSerializer, ProduitSerializer,
    ArtisanImageSerializer, LocationUpdateSerializer,
    ProduitCreateUpdateSerializer, ImageProduitSerializer,
    RegisterSerializer, LoginSerializer, UserSerializer,
    ChangePasswordSerializer, UserProfileSerializer
)
from .serializers import (
    RegisterSerializer, LoginSerializer, UserSerializer,
    ChangePasswordSerializer, UserProfileSerializer
)
from .models import UserProfile, Artisan


class CategorieViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour les catégories (lecture seule)
    """
    queryset = Categorie.objects.filter(actif=True)
    serializer_class = CategorieSerializer
    permission_classes = [AllowAny]
    
    @action(detail=True, methods=['get'])
    def rubriques(self, request, pk=None):
        """Récupérer les rubriques d'une catégorie"""
        categorie = self.get_object()
        rubriques = Rubrique.objects.filter(categorie=categorie, actif=True)
        serializer = RubriqueSerializer(rubriques, many=True)
        return Response(serializer.data)


class RubriqueViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour les rubriques (lecture seule)
    """
    queryset = Rubrique.objects.filter(actif=True)
    serializer_class = RubriqueSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['categorie']


class ArtisanViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les artisans
    - Liste publique (GET /artisans/)
    - Détail public (GET /artisans/{id}/)
    - Mon profil (GET /artisans/me/)
    - Créer profil (POST /artisans/)
    - Modifier profil (PUT/PATCH /artisans/{id}/)
    - Mettre à jour localisation (POST /artisans/{id}/update-location/)
    - Toggle visibilité (POST /artisans/{id}/toggle-visibility/)
    """
    queryset = Artisan.objects.select_related(
        'categorie', 'rubrique', 'user', 'statistiques'
    ).prefetch_related('produits', 'images')
    
    filter_backends = [
        DjangoFilterBackend, 
        filters.SearchFilter, 
        filters.OrderingFilter
    ]
    filterset_fields = ['categorie', 'rubrique', 'ville', 'pays', 'actif']
    search_fields = ['nom_entreprise', 'description', 'ville']
    ordering_fields = ['date_creation', 'nom_entreprise']
    ordering = ['-date_creation']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ArtisanListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ArtisanCreateUpdateSerializer
        return ArtisanDetailSerializer
    
    def get_permissions(self):
        """
        - Liste et détail : accessible à tous
        - Création, modification : authentification requise
        """
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        """
        - Liste publique : seulement les artisans actifs
        - Mon profil : tous les artisans de l'utilisateur
        """
        if self.action == 'list':
            return self.queryset.filter(actif=True)
        return self.queryset
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Récupérer le profil de l'artisan connecté"""
        try:
            artisan = request.user.artisan
            serializer = ArtisanDetailSerializer(artisan)
            return Response(serializer.data)
        except Artisan.DoesNotExist:
            return Response(
                {'detail': 'Vous n\'avez pas de profil artisan'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def update_location(self, request, pk=None):
        """Mettre à jour la localisation de l'artisan"""
        artisan = self.get_object()
        
        # Vérifier que c'est bien l'artisan propriétaire
        if artisan.user != request.user:
            return Response(
                {'detail': 'Permission refusée'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = LocationUpdateSerializer(
            artisan, 
            data=request.data, 
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'detail': 'Localisation mise à jour',
                'data': serializer.data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def toggle_visibility(self, request, pk=None):
        """Activer/Désactiver la visibilité du profil"""
        artisan = self.get_object()
        
        # Vérifier que c'est bien l'artisan propriétaire
        if artisan.user != request.user:
            return Response(
                {'detail': 'Permission refusée'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        artisan.actif = not artisan.actif
        artisan.save()
        
        return Response({
            'detail': 'Visibilité mise à jour',
            'actif': artisan.actif
        })
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Récupérer les statistiques d'un artisan"""
        artisan = self.get_object()
        
        try:
            stats = artisan.statistiques
        except StatistiqueArtisan.DoesNotExist:
            # Créer les stats si elles n'existent pas
            stats = StatistiqueArtisan.objects.create(artisan=artisan)
        
        # Calculer la tendance (simulation)
        tendance = 12  # TODO: Calculer la vraie tendance
        
        return Response({
            'vues': stats.nombre_vues,
            'favoris': stats.nombre_favoris,
            'produits': artisan.produits.filter(actif=True).count(),
            'tendance': tendance
        })


class ProduitViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les produits d'un artisan
    """
    serializer_class = ProduitSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Récupérer les produits de l'artisan connecté"""
        return Produit.objects.filter(artisan__user=self.request.user)
    
    def perform_create(self, serializer):
        """Créer un produit pour l'artisan connecté"""
        try:
            artisan = self.request.user.artisan
            serializer.save(artisan=artisan)
        except Artisan.DoesNotExist:
            raise serializers.ValidationError(
                "Vous devez créer un profil artisan d'abord"
            )


class ArtisanImageViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les images d'un artisan
    """
    serializer_class = ArtisanImageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Récupérer les images de l'artisan connecté"""
        return ArtisanImage.objects.filter(artisan__user=self.request.user)
    
    def perform_create(self, serializer):
        """Ajouter une image pour l'artisan connecté"""
        try:
            artisan = self.request.user.artisan
            serializer.save(artisan=artisan)
        except Artisan.DoesNotExist:
            raise serializers.ValidationError(
                "Vous devez créer un profil artisan d'abord"
            )