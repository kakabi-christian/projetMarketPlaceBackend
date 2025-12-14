from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers

from .models import (
    Categorie, Rubrique, Artisan,
    Produit, ArtisanImage, StatistiqueArtisan, ImageProduit
)
from .serializers import (
    CategorieSerializer, RubriqueSerializer,
    ArtisanListSerializer, ArtisanDetailSerializer,
    ArtisanCreateUpdateSerializer, ProduitSerializer,
    ArtisanImageSerializer, LocationUpdateSerializer,
    ProduitCreateUpdateSerializer, ImageProduitSerializer
)


@api_view(['GET'])
def homepage(request):
    return Response({
        'message': 'Marketplace API - Backend prêt pour React',
        'endpoints': {
            'categories': '/api/categories/',
            'artisans': '/api/artisans/',
            'rubriques': '/api/rubriques/',
            'admin': '/admin/'
        }
    })


class CategorieViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Categorie.objects.filter(actif=True)
    serializer_class = CategorieSerializer
    permission_classes = [AllowAny]

    @action(detail=True, methods=['get'])
    def rubriques(self, request, pk=None):
        categorie = self.get_object()
        rubriques = Rubrique.objects.filter(categorie=categorie, actif=True)
        serializer = RubriqueSerializer(rubriques, many=True)
        return Response(serializer.data)


class RubriqueViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Rubrique.objects.filter(actif=True)
    serializer_class = RubriqueSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['categorie']


# ✅ ARTISAN VIEWSET - COMPLÈTE ET CORRIGÉE
class ArtisanViewSet(viewsets.ModelViewSet):
    queryset = Artisan.objects.select_related(
        'categorie', 'rubrique', 'user'
    ).prefetch_related('produits', 'images')
    
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
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
        # ✅ Autoriser création SANS authentification
        if self.action in ['create', 'list', 'retrieve', 'stats', 'me', 'update_location', 'toggle_visibility', 'produits']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        if self.action == 'list':
            return self.queryset.filter(actif=True)
        return self.queryset

    def create(self, request, *args, **kwargs):
        """Crée un artisan SANS nécessiter de user"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        validated_data = serializer.validated_data
        
        artisan = Artisan.objects.create(
            nom_entreprise=validated_data['nom_entreprise'],
            nom_proprietaire=validated_data['nom_proprietaire'],
            description=validated_data.get('description', ''),
            categorie=validated_data['categorie'],
            rubrique=validated_data.get('rubrique'),
            ville=validated_data['ville'],
            telephone=validated_data.get('telephone', ''),
            email=validated_data.get('email', ''),
            pays=validated_data.get('pays', 'Cameroun'),
            adresse=validated_data.get('adresse', ''),
            actif=True,
            user=None
        )
        
        if 'logo' in request.FILES:
            artisan.logo = request.FILES['logo']
            artisan.save()
        
        StatistiqueArtisan.objects.get_or_create(artisan=artisan)
        
        response_serializer = ArtisanDetailSerializer(artisan)
        
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def me(self, request):
        """Récupère le dernier artisan créé"""
        try:
            artisan = Artisan.objects.latest('date_creation')
            serializer = ArtisanDetailSerializer(artisan)
            return Response(serializer.data)
        except Artisan.DoesNotExist:
            return Response(
                {'detail': "Aucun profil artisan trouvé"},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def update_location(self, request, pk=None):
        """Met à jour la localisation"""
        artisan = self.get_object()
        
        serializer = LocationUpdateSerializer(data=request.data)
        if serializer.is_valid():
            artisan.localisation_latitude = serializer.validated_data['latitude']
            artisan.localisation_longitude = serializer.validated_data['longitude']
            artisan.adresse = serializer.validated_data.get('adresse', artisan.adresse)
            artisan.save()
            return Response({
                'detail': 'Localisation mise à jour', 
                'success': True,
                'data': {
                    'latitude': float(artisan.localisation_latitude),
                    'longitude': float(artisan.localisation_longitude),
                    'adresse': artisan.adresse
                }
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def toggle_visibility(self, request, pk=None):
        """Toggle la visibilité de l'artisan"""
        artisan = self.get_object()
        artisan.actif = not artisan.actif
        artisan.save()
        return Response({
            'detail': 'Visibilité mise à jour', 
            'actif': artisan.actif
        })

    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def stats(self, request, pk=None):
        """Récupère les statistiques d'un artisan"""
        artisan = self.get_object()
        stats, _ = StatistiqueArtisan.objects.get_or_create(artisan=artisan)
        return Response({
            'vues': stats.nombre_vues,
            'favoris': stats.nombre_favoris,
            'produits': artisan.produits.filter(disponible=True).count(),
            'tendance': 12
        })

    # ✅ CORRECTION IMPORTANTE : L'INDENTATION ÉTAIT INCORRECTE
    @action(detail=True, methods=['get', 'post'], permission_classes=[AllowAny])
    def produits(self, request, pk=None):
        """Liste et création de produits d'un artisan"""
        artisan = self.get_object()
        
        if request.method == 'GET':
            # Liste les produits
            produits = artisan.produits.all().order_by('-date_creation')
            serializer = ProduitSerializer(produits, many=True)
            return Response(serializer.data)
        
        elif request.method == 'POST':
            # ✅ Création d'un nouveau produit
            serializer = ProduitCreateUpdateSerializer(data=request.data)
            if serializer.is_valid():
                # Associer automatiquement l'artisan
                produit = serializer.save(artisan=artisan)
                
                # Retourner avec le serializer de lecture
                response_serializer = ProduitSerializer(produit)
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ✅ PRODUIT VIEWSET
class ProduitViewSet(viewsets.ModelViewSet):
    queryset = Produit.objects.all().select_related('artisan', 'categorie').prefetch_related('images')
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ProduitCreateUpdateSerializer
        return ProduitSerializer

    def perform_create(self, serializer):
        """Création avec gestion des images"""
        serializer.save()

    def perform_update(self, serializer):
        """Mise à jour avec gestion des images"""
        serializer.save()

    @action(detail=True, methods=['delete'], url_path='images/(?P<image_id>[^/.]+)')
    def delete_image(self, request, pk=None, image_id=None):
        """Supprimer une image spécifique d'un produit"""
        produit = self.get_object()
        try:
            image = ImageProduit.objects.get(id=image_id, produit=produit)
            image.delete()
            return Response(
                {'detail': 'Image supprimée avec succès'},
                status=status.HTTP_204_NO_CONTENT
            )
        except ImageProduit.DoesNotExist:
            return Response(
                {'detail': 'Image non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )


class ArtisanImageViewSet(viewsets.ModelViewSet):
    serializer_class = ArtisanImageSerializer
    permission_classes = [AllowAny]
    queryset = ArtisanImage.objects.all()

    def perform_create(self, serializer):
        try:
            artisan = Artisan.objects.latest('date_creation')
            serializer.save(artisan=artisan)
        except Artisan.DoesNotExist:
            raise serializers.ValidationError("Aucun artisan trouvé")