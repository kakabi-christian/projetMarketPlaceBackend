# serializers.py - VERSION COMPLÈTE FINALE

from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    Categorie, Rubrique, Artisan,
    Produit, ArtisanImage, StatistiqueArtisan,
    ImageProduit, UserProfile, ProfilClient, Conversation,Message
)

class CategorieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categorie
        fields = ['id', 'nom_categorie', 'description', 'actif']


class RubriqueSerializer(serializers.ModelSerializer):
    categorie_nom = serializers.CharField(source='categorie.nom_categorie', read_only=True)
    class Meta:
        model = Rubrique
        fields = ['id', 'nom_rubrique', 'description', 'categorie', 'categorie_nom', 'actif']


class ImageProduitSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageProduit
        fields = ['id', 'image', 'ordre', 'date_ajout']
        read_only_fields = ['date_ajout']


class ProduitSerializer(serializers.ModelSerializer):
    images = ImageProduitSerializer(many=True, read_only=True)
    categorie = serializers.SerializerMethodField()
    artisan_nom = serializers.CharField(source='artisan.nom_entreprise', read_only=True)
    
    class Meta:
        model = Produit
        fields = ['id', 'nom', 'description', 'prix', 'categorie', 'disponible', 
                  'date_creation', 'date_modification', 'images', 'artisan', 'artisan_nom']
        read_only_fields = ['date_creation', 'date_modification', 'artisan']

    def get_categorie(self, obj):
        if obj.categorie:
            return {'id': obj.categorie.id, 'nom_categorie': obj.categorie.nom_categorie}
        return None


class ProduitCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Produit
        fields = ['id', 'nom', 'description', 'prix', 'categorie', 'disponible']

    def validate_prix(self, value):
        if value <= 0:
            raise serializers.ValidationError("Le prix doit être supérieur à 0")
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        produit = Produit.objects.create(**validated_data)
        if request and hasattr(request, 'FILES'):
            self._handle_image_upload(produit, request.FILES)
        return produit

    def update(self, instance, validated_data):
        request = self.context.get('request')
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if request and hasattr(request, 'FILES'):
            self._handle_image_upload(instance, request.FILES)
        return instance

    def _handle_image_upload(self, produit, files):
        current_max_ordre = produit.images.count()
        image_keys = [key for key in files.keys() if 'image' in key.lower()]
        for index, key in enumerate(sorted(image_keys)):
            ImageProduit.objects.create(produit=produit, image=files[key], ordre=current_max_ordre + index)

    def to_representation(self, instance):
        return ProduitSerializer(instance, context=self.context).data


class ArtisanImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArtisanImage
        fields = ['id', 'image', 'type_image', 'date_upload']
        read_only_fields = ['date_upload']


class StatistiqueArtisanSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatistiqueArtisan
        fields = ['nombre_vues', 'nombre_favoris', 'derniere_mise_a_jour']


class ArtisanListSerializer(serializers.ModelSerializer):
    categorie = CategorieSerializer(read_only=True)
    rubrique = RubriqueSerializer(read_only=True)
    nombre_produits = serializers.SerializerMethodField()

    class Meta:
        model = Artisan
        fields = ['id', 'nom_entreprise', 'logo', 'description', 'categorie', 'rubrique', 
                  'ville', 'pays', 'actif', 'nombre_produits', 'has_location']

    def get_nombre_produits(self, obj):
        return obj.produits.filter(disponible=True).count()


class ArtisanDetailSerializer(serializers.ModelSerializer):
    categorie = CategorieSerializer(read_only=True)
    rubrique = RubriqueSerializer(read_only=True)
    produits = ProduitSerializer(many=True, read_only=True)
    images = ArtisanImageSerializer(many=True, read_only=True)
    statistiques = StatistiqueArtisanSerializer(read_only=True)

    class Meta:
        model = Artisan
        fields = ['id', 'nom_entreprise', 'nom_proprietaire', 'description', 'logo', 
                  'categorie', 'rubrique', 'pays', 'ville', 'adresse',
                  'localisation_latitude', 'localisation_longitude', 'telephone', 'email', 
                  'site_web', 'actif', 'date_creation', 'date_modification',
                  'produits', 'images', 'statistiques', 'has_location']


class ArtisanCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artisan
        fields = ['id', 'uuid', 'nom_entreprise', 'nom_proprietaire', 'description', 'logo',
                  'categorie', 'rubrique', 'pays', 'ville', 'adresse', 'telephone', 'email', 'actif']
        read_only_fields = ['id', 'uuid']

    def validate_description(self, value):
        if len(value) < 50:
            raise serializers.ValidationError("La description doit contenir au moins 50 caractères.")
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        if hasattr(user, 'artisan'):
            raise serializers.ValidationError("Vous avez déjà un profil artisan.")
        artisan = Artisan.objects.create(user=user, **validated_data)
        StatistiqueArtisan.objects.create(artisan=artisan)
        return artisan


class LocationUpdateSerializer(serializers.Serializer):
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    adresse = serializers.CharField(max_length=300, required=False, allow_blank=True)


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['role', 'telephone', 'photo', 'date_naissance', 'adresse', 'ville', 
                  'pays', 'profile_artisan_complete']
        read_only_fields = ['profile_artisan_complete']


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile']


class ProfilClientSerializer(serializers.ModelSerializer):
    categories_preferees = CategorieSerializer(many=True, read_only=True)
    categories_preferees_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Categorie.objects.all(), source='categories_preferees',
        write_only=True, required=False
    )
    user_info = serializers.SerializerMethodField()
    nombre_favoris = serializers.ReadOnlyField()
    
    class Meta:
        model = ProfilClient
        fields = ['id', 'user', 'user_info', 'categories_preferees', 'categories_preferees_ids',
                  'ville_preference', 'pays_preference', 'rayon_recherche_km',
                  'budget_min', 'budget_max', 'recevoir_nouveautes', 'recevoir_promotions',
                  'bio', 'nombre_favoris', 'date_creation', 'date_modification']
        read_only_fields = ['user', 'date_creation', 'date_modification', 'nombre_favoris']
    
    def get_user_info(self, obj):
        return {
            'username': obj.user.username,
            'email': obj.user.email,
            'nom_complet': obj.user.get_full_name(),
            'first_name': obj.user.first_name,
            'last_name': obj.user.last_name,
            'photo': obj.user.profile.photo.url if obj.user.profile.photo else None,
        }


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES, write_only=True, required=True)
    telephone = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'first_name', 'last_name', 'role', 'telephone']
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True},
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Les mots de passe ne correspondent pas."})
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "Cet email est déjà utilisé."})
        if User.objects.filter(username=attrs['username']).exists():
            raise serializers.ValidationError({"username": "Ce nom d'utilisateur est déjà pris."})
        return attrs
    
    def create(self, validated_data):
        password2 = validated_data.pop('password2')
        role = validated_data.pop('role')
        telephone = validated_data.pop('telephone', '')
        
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        
        # Créer le profil manuellement
        profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={'role': role, 'telephone': telephone}
        )
        
        if not created:
            profile.role = role
            profile.telephone = telephone
            profile.save()
        
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    
    def validate(self, attrs):
        user = authenticate(username=attrs.get('username'), password=attrs.get('password'))
        if user is None:
            raise serializers.ValidationError({"detail": "Identifiants incorrects."})
        if not user.is_active:
            raise serializers.ValidationError({"detail": "Ce compte est désactivé."})
        attrs['user'] = user
        return attrs
    
    def create(self, validated_data):
        user = validated_data['user']
        refresh = RefreshToken.for_user(user)
        return {
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    new_password2 = serializers.CharField(required=True, write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password": "Les nouveaux mots de passe ne correspondent pas."})
        return attrs
    
class MessageSerializer(serializers.ModelSerializer):
    expediteur_nom = serializers.SerializerMethodField()
    est_moi = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = ['id', 'contenu', 'date_envoi', 'lu', 'expediteur', 
                  'expediteur_nom', 'est_moi']
        read_only_fields = ['expediteur', 'date_envoi']
    
    def get_expediteur_nom(self, obj):
        return obj.expediteur.get_full_name() or obj.expediteur.username
    
    def get_est_moi(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return obj.expediteur.id == request.user.id
        return False


class ConversationSerializer(serializers.ModelSerializer):
    artisan_info = serializers.SerializerMethodField()
    client_info = serializers.SerializerMethodField()
    dernier_message = serializers.SerializerMethodField()
    non_lus = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = ['id', 'artisan', 'client', 'artisan_info', 'client_info',
                  'date_creation', 'derniere_activite', 'dernier_message', 
                  'non_lus', 'client_non_lu', 'artisan_non_lu']
    
    def get_artisan_info(self, obj):
        return {
            'id': obj.artisan.id,
            'nom': obj.artisan.nom_entreprise,
            'logo': obj.artisan.logo.url if obj.artisan.logo else None,
            'ville': obj.artisan.ville,
        }
    
    def get_client_info(self, obj):
        return {
            'id': obj.client.id,
            'nom': obj.client.get_full_name() or obj.client.username,
            'email': obj.client.email,
        }
    
    def get_dernier_message(self, obj):
        dernier = obj.messages.last()
        if dernier:
            return {
                'contenu': dernier.contenu[:50],
                'date': dernier.date_envoi,
                'expediteur': dernier.expediteur.id
            }
        return None
    
    def get_non_lus(self, obj):
        request = self.context.get('request')
        if request and request.user:
            # Si client, retourne ses non-lus
            if request.user.id == obj.client.id:
                return obj.client_non_lu
            # Si artisan, retourne ses non-lus
            return obj.artisan_non_lu
        return 0
