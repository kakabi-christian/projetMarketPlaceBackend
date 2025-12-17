from django.shortcuts import render

from django.contrib.auth.models import User
from django.contrib.auth import update_session_auth_hash
from django.db.models import Count, Sum, Q
from datetime import datetime, timedelta
from rest_framework.permissions import IsAdminUser
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer
from rest_framework import viewsets, generics, status, permissions, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken 
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import login, authenticate

# ✅ TOUS LES MODÈLES
from .models import (
    Categorie, Rubrique, Artisan, Produit, ArtisanImage, 
    StatistiqueArtisan, ImageProduit, UserProfile, 
    ProfilClient, Favori,   # ✅ Favori ajouté
)

# ✅ TOUS LES SERIALIZERS
from .serializers import (
    CategorieSerializer, RubriqueSerializer, ArtisanListSerializer,
    ArtisanDetailSerializer, ArtisanCreateUpdateSerializer, 
    ProduitSerializer, ArtisanImageSerializer, LocationUpdateSerializer,
    ProduitCreateUpdateSerializer, ImageProduitSerializer,
    RegisterSerializer, LoginSerializer, UserSerializer,
    ChangePasswordSerializer, UserProfileSerializer, ProfilClientSerializer
)

@api_view(['GET'])
def homepage(request):
    return Response({
        'message': 'Marketplace API - Backend prêt pour React',
        'endpoints': {
            'categories': '/api/categories/',
            'artisans': '/api/artisans/',
            'rubriques': '/api/rubriques/',
            'profils-clients/me/': '/api/profils-clients/me/',
            'auth/me/': '/api/auth/me/'
        }
    })

# ✅ CATEGORIE VIEWSET
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

# Dans views.py - REMPLACE ProfilClientViewSet par ceci :

class ProfilClientViewSet(viewsets.ModelViewSet):
    serializer_class = ProfilClientSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ProfilClient.objects.filter(user=self.request.user)

    @action(detail=False, methods=['GET', 'POST', 'PUT', 'PATCH'], url_path='me')
    def me(self, request):
        """CRUD du profil client connecté"""
        
        if request.method == 'GET':
            # ✅ RÉCUPÉRER LE PROFIL
            try:
                profil = ProfilClient.objects.select_related('user').prefetch_related(
                    'categories_preferees'  # ✅ IMPORTANT : Charger les catégories
                ).get(user=request.user)
                
                serializer = self.get_serializer(profil)
                data = serializer.data
                
                # ✅ Debug : Afficher ce qu'on renvoie
                print(f"✅ Profil récupéré pour {request.user.username}")
                print(f"📂 Catégories préférées: {[cat['nom_categorie'] for cat in data.get('categories_preferees', [])]}")
                
                return Response(data)
                
            except ProfilClient.DoesNotExist:
                return Response(
                    {'detail': 'Profil client non trouvé. Créez-le d\'abord.'},
                    status=404
                )
        
        elif request.method in ['POST', 'PUT', 'PATCH']:
            # ✅ CRÉER OU METTRE À JOUR
            try:
                profil = ProfilClient.objects.get(user=request.user)
                # Mise à jour
                serializer = self.get_serializer(profil, data=request.data, partial=(request.method == 'PATCH'))
            except ProfilClient.DoesNotExist:
                # Création
                serializer = self.get_serializer(data=request.data)
            
            serializer.is_valid(raise_exception=True)
            
            # ✅ Sauvegarder avec l'utilisateur
            profil = serializer.save(user=request.user)
            
            # ✅ Gérer les catégories préférées
            categories_ids = request.data.get('categories_preferees_ids', [])
            if categories_ids:
                print(f"📝 Sauvegarde {len(categories_ids)} catégories pour {request.user.username}")
                profil.categories_preferees.set(categories_ids)
            
            # ✅ Retourner avec les catégories chargées
            profil.refresh_from_db()
            response_serializer = self.get_serializer(profil)
            
            print(f"✅ Profil sauvegardé avec {profil.categories_preferees.count()} catégories")
            
            return Response(response_serializer.data, status=201 if request.method == 'POST' else 200)
    
    @action(detail=False, methods=['GET', 'POST', 'DELETE'], url_path='favoris')
    def favoris(self, request):
        """Gestion des favoris"""
        
        if request.method == 'GET':
            # Liste des favoris
            favoris = Favori.objects.filter(client=request.user).select_related('artisan__categorie')
            artisans = [f.artisan for f in favoris]
            serializer = ArtisanListSerializer(artisans, many=True)
            return Response(serializer.data)

        elif request.method == 'POST':
            # Ajouter favori
            artisan_id = request.data.get('artisan_id')
            try:
                artisan = Artisan.objects.get(id=artisan_id)
                Favori.objects.get_or_create(client=request.user, artisan=artisan)
                return Response({'message': '✅ Ajouté aux favoris'})
            except Artisan.DoesNotExist:
                return Response({'error': 'Artisan introuvable'}, status=404)

        elif request.method == 'DELETE':
            # Supprimer favori
            artisan_id = request.data.get('artisan_id')
            try:
                Favori.objects.filter(client=request.user, artisan_id=artisan_id).delete()
                return Response({'message': '✅ Retiré des favoris'})
            except:
                return Response({'error': 'Favori introuvable'}, status=404)
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
        # ✅ Endpoints publics vs authentifiés
        if self.action in ['list', 'retrieve', 'stats', 'produits', 'images']:
            return [AllowAny()]
        elif self.action in ['create', 'me', 'update_location', 'toggle_visibility']:
            return [IsAuthenticated()]
        return [IsAuthenticated()]

    def get_queryset(self):
        if self.action == 'list':
            return self.queryset.filter(actif=True)
        return self.queryset

    def create(self, request, *args, **kwargs):
        """Crée un artisan lié à l'utilisateur connecté"""
        
        # ✅ VÉRIFIER L'AUTHENTIFICATION
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Vous devez être connecté pour créer un profil artisan'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # ✅ VÉRIFIER QU'IL N'A PAS DÉJÀ UN ARTISAN
        if Artisan.objects.filter(user=request.user).exists():
            existing = Artisan.objects.get(user=request.user)
            return Response(
                {
                    'detail': 'Vous avez déjà un profil artisan',
                    'artisan_id': existing.id
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # ✅ VALIDER LES DONNÉES
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        
        # ✅ CRÉER L'ARTISAN AVEC LE USER CONNECTÉ
        artisan = Artisan.objects.create(
            user=request.user,  # ✅ IMPORTANT : lier au user connecté
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
            actif=True
        )
        
        # ✅ GÉRER LE LOGO SI PRÉSENT
        if 'logo' in request.FILES:
            artisan.logo = request.FILES['logo']
            artisan.save()
        
        # ✅ CRÉER LES STATISTIQUES
        StatistiqueArtisan.objects.get_or_create(artisan=artisan)
        
        # ✅ LOG
        print(f"✅ Artisan créé: ID={artisan.id}, Nom={artisan.nom_entreprise}, User={request.user.username} (ID={request.user.id})")
        
        # ✅ RETOURNER LA RÉPONSE
        response_serializer = ArtisanDetailSerializer(artisan)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Récupère l'artisan lié à l'utilisateur connecté"""
        print(f"🔍 Artisan ME - User: {request.user.username} (ID: {request.user.id})")
        
        try:
            artisan = Artisan.objects.get(user=request.user)
            print(f"✅ Artisan trouvé: {artisan.nom_entreprise} (ID: {artisan.id})")
            
            serializer = ArtisanDetailSerializer(artisan)
            return Response(serializer.data)
            
        except Artisan.DoesNotExist:
            print(f"❌ Aucun artisan trouvé pour user {request.user.username}")
            return Response(
                {'detail': "Vous n'avez pas encore créé votre profil artisan"},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def update_location(self, request, pk=None):
        """Met à jour la localisation"""
        artisan = self.get_object()
        
        # ✅ Vérifier que l'artisan appartient à l'utilisateur
        if artisan.user != request.user:
            return Response(
                {'detail': "Vous n'avez pas la permission de modifier cet artisan"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = LocationUpdateSerializer(data=request.data)
        if serializer.is_valid():
            artisan.localisation_latitude = serializer.validated_data['latitude']
            artisan.localisation_longitude = serializer.validated_data['longitude']
            artisan.adresse = serializer.validated_data.get('adresse', artisan.adresse)
            artisan.save()
            
            print(f"✅ Localisation mise à jour pour artisan {artisan.id}")
            
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

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def toggle_visibility(self, request, pk=None):
        """Toggle la visibilité de l'artisan"""
        artisan = self.get_object()
        
        # ✅ Vérifier que l'artisan appartient à l'utilisateur
        if artisan.user != request.user:
            return Response(
                {'detail': "Vous n'avez pas la permission de modifier cet artisan"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        artisan.actif = not artisan.actif
        artisan.save()
        
        print(f"✅ Visibilité artisan {artisan.id}: {artisan.actif}")
        
        return Response({
            'detail': 'Visibilité mise à jour', 
            'actif': artisan.actif
        })
    # 🔍 CHERCHE CETTE MÉTHODE et REMPLACE-LA
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

    @action(detail=True, methods=['get', 'post'], permission_classes=[AllowAny])
    def produits(self, request, pk=None):
        """Liste et création de produits d'un artisan"""
        artisan = self.get_object()
        
        if request.method == 'GET':
            produits = artisan.produits.all().order_by('-date_creation')
            serializer = ProduitSerializer(produits, many=True)
            return Response(serializer.data)
        
        elif request.method == 'POST':
            # ✅ Vérifier que l'artisan appartient à l'utilisateur
            if not request.user.is_authenticated:
                return Response(
                    {'detail': "Vous devez être connecté"},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            if artisan.user != request.user:
                return Response(
                    {'detail': "Vous n'avez pas la permission d'ajouter des produits"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = ProduitCreateUpdateSerializer(data=request.data)
            if serializer.is_valid():
                produit = serializer.save(artisan=artisan)
                print(f"✅ Produit créé: {produit.nom} pour artisan {artisan.id}")
                
                response_serializer = ProduitSerializer(produit)
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def images(self, request, pk=None):
        """Liste toutes les images d'un artisan spécifique"""
        artisan = self.get_object()
        images = artisan.images.all().order_by('-date_creation')[:12]
        serializer = ArtisanImageSerializer(images, many=True)
        return Response(serializer.data)

class LoginView(APIView):
    """Connexion utilisateur avec gestion correcte des artisans"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # ✅ Récupération des données
        data = serializer.save()
        user_data = data['user']
        real_user = User.objects.get(id=user_data['id'])
        login(request, real_user)
        
        print("=" * 80)
        print(f"🔐 LOGIN ATTEMPT")
        print(f"   Username: {request.data.get('username')}")
        print(f"   User ID: {real_user.id}")
        print(f"   User: {real_user.username}")
        print("=" * 80)
        
        profile_complete = True
        artisan_id = None
        user_role = user_data['profile']['role']
        
        print(f"🎭 Role détecté: {user_role}")
        
        # ✅ SI ARTISAN : Chercher SON artisan (pas le dernier créé)
        if user_role == 'artisan':
            try:
                # ✅ FIX CRITIQUE : .get(user=real_user) au lieu de .filter().first()
                artisan = Artisan.objects.get(user=real_user)
                artisan_id = artisan.id
                profile_complete = bool(
                    artisan.localisation_latitude and 
                    artisan.localisation_longitude
                )
                
                print(f"✅ ARTISAN TROUVÉ:")
                print(f"   ID: {artisan.id}")
                print(f"   Nom: {artisan.nom_entreprise}")
                print(f"   User ID: {artisan.user.id}")
                print(f"   Profil complet: {profile_complete}")
                
            except Artisan.DoesNotExist:
                print(f"⚠️ AUCUN ARTISAN pour user {real_user.username} (ID={real_user.id})")
                artisan_id = None
                profile_complete = False
            except Artisan.MultipleObjectsReturned:
                # ❌ Ce cas ne devrait JAMAIS arriver (un user = un artisan)
                print(f"❌ ERREUR: Plusieurs artisans pour user {real_user.username}!")
                artisan = Artisan.objects.filter(user=real_user).first()
                artisan_id = artisan.id if artisan else None
                profile_complete = False
        
        print("=" * 80)
        
        response_data = {
            'message': 'Connexion réussie !',
            'user': user_data,
            'tokens': data['tokens'],
            'artisan_id': artisan_id,
            'next_step': self._get_next_step(user_data, profile_complete, user_role)
        }
        
        print(f"📤 RESPONSE:")
        print(f"   artisan_id: {artisan_id}")
        print(f"   redirect: {response_data['next_step']['redirect']}")
        print("=" * 80)
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    def _get_next_step(self, user, profile_complete=True, user_role=None):
        """Détermine la prochaine étape selon le rôle et l'état du profil"""
        role = user_role or user['profile']['role']
        
        if role == 'artisan':
            if not profile_complete:
                return {
                    'action': 'complete_profile',
                    'message': 'Complétez votre profil artisan',
                    'redirect': '/artisan/create'
                }
            return {
                'action': 'artisan_dashboard',
                'message': 'Bienvenue sur votre tableau de bord',
                'redirect': '/artisan/dashboard'
            }
        elif role == 'client':
            return {
                'action': 'client_dashboard',
                'message': 'Bienvenue sur votre espace client',
                'redirect': '/client/dashboard'
            }
        elif role == 'admin':
            return {
                'action': 'admin_dashboard',
                'message': 'Accédez au panneau d\'administration',
                'redirect': '/admin/dashboard'
            }
        
        return {
            'action': 'home',
            'message': 'Bienvenue',
            'redirect': '/'
        }
   
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
        

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # ✅ 1️⃣ CRÉER USER
        user = serializer.save()
        
        # ✅ 2️⃣ CRÉER Profile IMMÉDIATEMENT (AVANT accès user.profile)
        profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'role': 'client',  # Par défaut client
                'telephone': request.data.get('telephone', ''),
                'ville': request.data.get('ville', 'Yaoundé')
            }
        )
        
        # ✅ 3️⃣ User data SANS crash
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'profile': {
                'id': profile.id,
                'role': profile.role
            }
        }
        
        refresh = RefreshToken.for_user(user)
        return Response({
            'message': '✅ User + Profile créés !',
            'user': user_data,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            }
        }, status=201)



class LogoutView(APIView):
    """
    Vue pour la déconnexion
    POST /api/auth/logout/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Optionnel : Blacklister le refresh token si vous utilisez simplejwt
            refresh_token = request.data.get("refresh_token")
            if refresh_token:
                from rest_framework_simplejwt.tokens import RefreshToken
                token = RefreshToken(refresh_token)
                token.blacklist()
        except Exception:
            pass
        
        return Response({
            'message': 'Déconnexion réussie'
        }, status=status.HTTP_200_OK)


class MeView(APIView):
    """
    Vue pour récupérer l'utilisateur connecté
    GET /api/auth/me/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user_data = UserSerializer(request.user).data
        
        # Ajouter l'ID de l'artisan si c'est un artisan
        if request.user.profile.role == 'artisan':
            try:
                artisan = Artisan.objects.get(user=request.user)
                user_data['artisan_id'] = artisan.id
                user_data['profile']['profile_artisan_complete'] = bool(
                    artisan.localisation_latitude and 
                    artisan.localisation_longitude
                )
            except Artisan.DoesNotExist:
                user_data['artisan_id'] = None
                user_data['profile']['profile_artisan_complete'] = False
        
        return Response(user_data)


class ChangePasswordView(APIView):
    """
    Vue pour changer le mot de passe
    POST /api/auth/change-password/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        
        # Vérifier l'ancien mot de passe
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({
                'old_password': ['Mot de passe incorrect.']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Changer le mot de passe
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        # Mettre à jour la session
        update_session_auth_hash(request, user)
        
        return Response({
            'message': 'Mot de passe modifié avec succès'
        }, status=status.HTTP_200_OK)


class UpdateProfileView(APIView):
    """
    Vue pour mettre à jour le profil utilisateur
    PUT/PATCH /api/auth/profile/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Récupérer le profil"""
        serializer = UserProfileSerializer(request.user.profile)
        return Response(serializer.data)
    
    def patch(self, request):
        """Mise à jour partielle"""
        serializer = UserProfileSerializer(
            request.user.profile,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'message': 'Profil mis à jour',
            'profile': serializer.data
        })
    
class AdminStatsView(APIView):
    """Statistiques générales (admin uniquement)"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        print(f"🔐 Admin Stats - User: {request.user.username}")
        
        # Vérifier que c'est un admin
        try:
            if request.user.profile.role != 'admin' and not request.user.is_superuser:
                return Response({'detail': 'Permission refusée'}, status=403)
            print(f"🎭 Role: {request.user.profile.role}")
        except UserProfile.DoesNotExist:
            return Response({'detail': 'Profil utilisateur manquant'}, status=403)
        
        # ✅ STATS DE BASE
        total_users = User.objects.count()
        total_artisans = Artisan.objects.count()
        total_produits = Produit.objects.count()
        total_clients = User.objects.filter(profile__role='client').count()
        artisans_actifs = Artisan.objects.filter(actif=True).count()
        produits_disponibles = Produit.objects.filter(disponible=True).count()
        
        # ✅ NOUVEAUX CE MOIS
        from django.utils import timezone
        debut_mois = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        nouveaux_users_mois = User.objects.filter(date_joined__gte=debut_mois).count()
        nouveaux_artisans_mois = Artisan.objects.filter(date_creation__gte=debut_mois).count()
        
        # ✅ RÉPARTITION PAR CATÉGORIE (IMPORTANT POUR LES GRAPHIQUES)
        categories = Categorie.objects.annotate(
            count=Count('artisans')  # ✅ PLURIEL : related_name dans le modèle
        ).filter(count__gt=0).values('nom_categorie', 'count').order_by('-count')[:5]
        
        categories_list = [
            {'nom': cat['nom_categorie'], 'count': cat['count']} 
            for cat in categories
        ]
        
        print(f"📊 Catégories: {categories_list}")
        
        # ✅ RÉPARTITION PAR VILLE (IMPORTANT POUR LES GRAPHIQUES)
        villes = Artisan.objects.values('ville').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        villes_list = [
            {'nom': ville['ville'], 'count': ville['count']} 
            for ville in villes
        ]
        
        print(f"🏙️ Villes: {villes_list}")
        
        # ✅ DERNIERS UTILISATEURS
        recent_users = []
        for user in User.objects.order_by('-date_joined')[:5]:
            try:
                role = user.profile.role
            except UserProfile.DoesNotExist:
                role = 'N/A'
            
            recent_users.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': role,
                'date_inscription': user.date_joined.isoformat() if user.date_joined else None
            })
        
        # ✅ STATS VUES & FAVORIS
        total_vues = sum(stat.nombre_vues for stat in StatistiqueArtisan.objects.all())
        total_favoris = Favori.objects.count()
        
        response_data = {
            'total_users': total_users,
            'total_artisans': total_artisans,
            'total_produits': total_produits,
            'total_clients': total_clients,
            'artisans_actifs': artisans_actifs,
            'produits_disponibles': produits_disponibles,
            'nouveaux_users_mois': nouveaux_users_mois,
            'nouveaux_artisans_mois': nouveaux_artisans_mois,
            'categories': categories_list,  # ✅ POUR LES GRAPHIQUES
            'villes': villes_list,  # ✅ POUR LES GRAPHIQUES
            'recent_users': recent_users,
            'total_vues': total_vues,
            'total_favoris': total_favoris,
        }
        
        print(f"📤 Response: {response_data}")
        
        return Response(response_data)


# Dans views.py - Version APIView corrigée

class AdminUserToggleActiveView(APIView):
    """Bloquer/Débloquer un utilisateur"""
    permission_classes = [IsAuthenticated]
    
    # ✅ AJOUTE http_method_names pour forcer POST
    http_method_names = ['post']
    
    def post(self, request, user_id):
        """Toggle is_active d'un utilisateur"""
        print(f"🔄 Toggle Active - User ID: {user_id}, Requester: {request.user.username}")
        
        try:
            if request.user.profile.role != 'admin' and not request.user.is_superuser:
                return Response({'detail': 'Permission refusée'}, status=403)
        except UserProfile.DoesNotExist:
            return Response({'detail': 'Profil manquant'}, status=403)
        
        try:
            user = User.objects.get(id=user_id)
            
            # Empêcher de se bloquer soi-même
            if user.id == request.user.id:
                return Response({
                    'detail': 'Vous ne pouvez pas vous bloquer vous-même'
                }, status=400)
            
            # Toggle l'état
            user.is_active = not user.is_active
            user.save()
            
            print(f"✅ User {user.username} - is_active: {user.is_active}")
            
            return Response({
                'detail': f'Utilisateur {"activé" if user.is_active else "bloqué"}',
                'is_active': user.is_active,
                'username': user.username
            })
            
        except User.DoesNotExist:
            return Response({'detail': 'Utilisateur non trouvé'}, status=404)
        except Exception as e:
            print(f"❌ Erreur toggle: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({'detail': f'Erreur: {str(e)}'}, status=500)

# ✅ 3. AdminUsersView - Gardez votre version actuelle
class AdminUsersView(APIView):
    """Liste tous les utilisateurs (admin uniquement)"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        print(f"🔐 Admin Users - User: {request.user.username}")
        
        # Vérifier que c'est un admin
        try:
            if request.user.profile.role != 'admin' and not request.user.is_superuser:
                return Response({'detail': 'Permission refusée'}, status=403)
        except UserProfile.DoesNotExist:
            return Response({'detail': 'Profil utilisateur manquant'}, status=403)
        
        users = User.objects.all().order_by('-date_joined')
        
        users_data = []
        for user in users:
            # ✅ PROTECTION contre profils manquants
            try:
                profile = user.profile
                role = profile.role
                telephone = profile.telephone or ''
            except UserProfile.DoesNotExist:
                # Créer automatiquement le profil manquant
                profile = UserProfile.objects.create(
                    user=user,
                    role='admin' if user.is_superuser else 'client'
                )
                role = profile.role
                telephone = ''
                print(f"✅ Profil auto-créé pour {user.username}")
            
            users_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': role,
                'telephone': telephone,
                'is_active': user.is_active,
                'is_superuser': user.is_superuser,
                'date_joined': user.date_joined.isoformat() if user.date_joined else None,
            })
        
        return Response({
            'users': users_data,
            'total': len(users_data)
        })


# ✅ 4. AdminUserDetailView - Gardez votre version actuelle
class AdminUserDetailView(APIView):
    """Détails et actions sur un utilisateur"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, user_id):
        """Récupérer les détails d'un utilisateur"""
        try:
            if request.user.profile.role != 'admin' and not request.user.is_superuser:
                return Response({'detail': 'Permission refusée'}, status=403)
        except UserProfile.DoesNotExist:
            return Response({'detail': 'Profil manquant'}, status=403)
        
        try:
            user = User.objects.get(id=user_id)
            
            # Profil
            try:
                profile = user.profile
                role = profile.role
                telephone = profile.telephone or ''
            except UserProfile.DoesNotExist:
                profile = UserProfile.objects.create(user=user, role='client')
                role = 'client'
                telephone = ''
            
            # Données associées
            artisan_data = None
            if role == 'artisan':
                try:
                    artisan = Artisan.objects.get(user=user)
                    artisan_data = {
                        'id': artisan.id,
                        'nom_entreprise': artisan.nom_entreprise,
                        'ville': artisan.ville,
                        'actif': artisan.actif
                    }
                except Artisan.DoesNotExist:
                    pass
            
            return Response({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': role,
                'telephone': telephone,
                'is_active': user.is_active,
                'date_joined': user.date_joined.isoformat() if user.date_joined else None,
                'artisan': artisan_data
            })
            
        except User.DoesNotExist:
            return Response({'detail': 'Utilisateur non trouvé'}, status=404)
    
    def patch(self, request, user_id):
        """Modifier un utilisateur"""
        try:
            if request.user.profile.role != 'admin' and not request.user.is_superuser:
                return Response({'detail': 'Permission refusée'}, status=403)
        except UserProfile.DoesNotExist:
            return Response({'detail': 'Profil manquant'}, status=403)
        
        try:
            user = User.objects.get(id=user_id)
            
            # Mise à jour des champs
            if 'is_active' in request.data:
                user.is_active = request.data['is_active']
            if 'email' in request.data:
                user.email = request.data['email']
            if 'first_name' in request.data:
                user.first_name = request.data['first_name']
            if 'last_name' in request.data:
                user.last_name = request.data['last_name']
            
            user.save()
            
            return Response({
                'detail': 'Utilisateur mis à jour',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'is_active': user.is_active
                }
            })
            
        except User.DoesNotExist:
            return Response({'detail': 'Utilisateur non trouvé'}, status=404)
    
    def delete(self, request, user_id):
        """Supprimer un utilisateur"""
        try:
            if request.user.profile.role != 'admin' and not request.user.is_superuser:
                return Response({'detail': 'Permission refusée'}, status=403)
        except UserProfile.DoesNotExist:
            return Response({'detail': 'Profil manquant'}, status=403)
        
        try:
            user = User.objects.get(id=user_id)
            
            # Empêcher la suppression de son propre compte
            if user.id == request.user.id:
                return Response({
                    'detail': 'Vous ne pouvez pas supprimer votre propre compte'
                }, status=400)
            
            username = user.username
            user.delete()
            
            return Response({
                'detail': f'Utilisateur {username} supprimé'
            }, status=200)
            
        except User.DoesNotExist:
            return Response({'detail': 'Utilisateur non trouvé'}, status=404)
        
class ConversationViewSet(viewsets.ModelViewSet):
    """Gestion des conversations - Client ET Artisan"""
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Retourne les conversations de l'utilisateur connecté"""
        user = self.request.user
        print(f"🔍 Conversations pour: {user.username} (ID={user.id})")
        
        # ✅ Si l'user est artisan, récupère via son profil artisan
        try:
            artisan = Artisan.objects.get(user=user)
            conversations = Conversation.objects.filter(artisan=artisan)
            print(f"✅ {conversations.count()} conversations artisan trouvées")
            return conversations
        except Artisan.DoesNotExist:
            pass
        
        # ✅ Si c'est un client, récupère via client
        conversations = Conversation.objects.filter(client=user)
        print(f"✅ {conversations.count()} conversations client trouvées")
        return conversations
    
    def create(self, request, *args, **kwargs):
        """Créer une conversation (CLIENT uniquement)"""
        print(f"📝 Création conversation par {request.user.username}")
        
        artisan_id = request.data.get('artisan_id')
        if not artisan_id:
            return Response(
                {'error': 'artisan_id requis'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            artisan = Artisan.objects.get(id=artisan_id)
            print(f"✅ Artisan trouvé: {artisan.nom_entreprise}")
        except Artisan.DoesNotExist:
            return Response(
                {'error': 'Artisan introuvable'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # ✅ Vérifier si conversation existe déjà
        conversation, created = Conversation.objects.get_or_create(
            artisan=artisan,
            client=request.user
        )
        
        if created:
            print(f"✅ Nouvelle conversation créée (ID={conversation.id})")
        else:
            print(f"ℹ️ Conversation existante retournée (ID={conversation.id})")
        
        serializer = self.get_serializer(conversation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    # ✅ MESSAGES D'UNE CONVERSATION
    @action(detail=True, methods=['get', 'post'], url_path='messages')
    def conversation_messages(self, request, pk=None):
        """GET = lire messages | POST = envoyer message"""
        conversation = self.get_object()
        user = request.user
        
        print(f"💬 Messages conv={pk} | User={user.username} | Method={request.method}")
        
        # ✅ VÉRIFIER PERMISSIONS
        try:
            artisan = Artisan.objects.get(user=user)
            is_artisan = conversation.artisan.id == artisan.id
        except Artisan.DoesNotExist:
            is_artisan = False
        
        is_client = conversation.client.id == user.id
        
        if not (is_artisan or is_client):
            print(f"❌ Permission refusée: ni artisan ni client")
            return Response(
                {'error': 'Accès refusé'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # ✅ GET : Lire les messages
        if request.method == 'GET':
            messages = conversation.messages.all().order_by('date_envoi')
            
            # Marquer comme lus
            if is_client:
                messages.filter(expediteur=conversation.artisan.user).update(lu=True)
                conversation.client_non_lu = 0
            elif is_artisan:
                messages.filter(expediteur=conversation.client).update(lu=True)
                conversation.artisan_non_lu = 0
            conversation.save()
            
            serializer = MessageSerializer(
                messages, 
                many=True, 
                context={'request': request}
            )
            print(f"✅ {len(serializer.data)} messages retournés")
            return Response(serializer.data)
        
        # ✅ POST : Envoyer un message
        elif request.method == 'POST':
            contenu = request.data.get('contenu', '').strip()
            if not contenu:
                return Response(
                    {'error': 'Message vide'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Créer le message
            message = Message.objects.create(
                conversation=conversation,
                expediteur=user,
                contenu=contenu
            )
            
            # ✅ Incrémenter compteur pour le destinataire
            if is_client:
                conversation.artisan_non_lu += 1
            elif is_artisan:
                conversation.client_non_lu += 1
            
            conversation.save()
            
            serializer = MessageSerializer(message, context={'request': request})
            print(f"✅ Message envoyé: {contenu[:50]}...")
            return Response(serializer.data, status=status.HTTP_201_CREATED)


# ============================================================================
# 3️⃣ LISTE CONVERSATIONS POUR ARTISAN
# ============================================================================

class ArtisanConversationsView(APIView):
    """Liste des conversations pour un artisan"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        print(f"📋 Liste conversations artisan: {request.user.username}")
        
        try:
            artisan = Artisan.objects.get(user=request.user)
            print(f"✅ Artisan: {artisan.nom_entreprise} (ID={artisan.id})")
        except Artisan.DoesNotExist:
            print("❌ Pas d'artisan pour cet user")
            return Response(
                {'error': 'Profil artisan introuvable'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        conversations = Conversation.objects.filter(
            artisan=artisan
        ).order_by('-derniere_activite')
        
        serializer = ConversationSerializer(
            conversations, 
            many=True, 
            context={'request': request}
        )
        
        print(f"✅ {len(serializer.data)} conversations trouvées")
        return Response(serializer.data)


# ============================================================================
# 4️⃣ DÉTAILS CONVERSATION (pour l'artisan)
# ============================================================================

class ArtisanConversationDetailView(APIView):
    """Détails d'une conversation spécifique pour artisan"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, conversation_id):
        print(f"🔍 Détails conv {conversation_id} pour {request.user.username}")
        
        try:
            artisan = Artisan.objects.get(user=request.user)
        except Artisan.DoesNotExist:
            return Response(
                {'error': 'Profil artisan introuvable'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            conversation = Conversation.objects.get(
                id=conversation_id,
                artisan=artisan
            )
        except Conversation.DoesNotExist:
            return Response(
                {'error': 'Conversation introuvable'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Messages
        messages = conversation.messages.all().order_by('date_envoi')
        
        # Marquer comme lus
        messages.filter(expediteur=conversation.client).update(lu=True)
        conversation.artisan_non_lu = 0
        conversation.save()
        
        serializer = MessageSerializer(
            messages, 
            many=True, 
            context={'request': request}
        )
        
        print(f"✅ {len(serializer.data)} messages")
        return Response(serializer.data)