from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Produit, ImageProduit
from .models import (
    Categorie, Rubrique, Artisan,
    Produit, ArtisanImage, StatistiqueArtisan,
)


class CategorieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categorie
        fields = ['id', 'nom_categorie', 'description', 'actif']


class RubriqueSerializer(serializers.ModelSerializer):
    categorie_nom = serializers.CharField(
        source='categorie.nom_categorie', read_only=True
    )

    class Meta:
        model = Rubrique
        fields = ['id', 'nom_rubrique', 'description',
                  'categorie', 'categorie_nom', 'actif']


class ImageProduitSerializer(serializers.ModelSerializer):
    """Serializer pour les images de produits"""
    class Meta:
        model = ImageProduit
        fields = ['id', 'image', 'ordre', 'date_ajout']
        read_only_fields = ['date_ajout']


class ProduitSerializer(serializers.ModelSerializer):
    """Serializer pour la lecture des produits"""
    images = ImageProduitSerializer(many=True, read_only=True)
    categorie = serializers.SerializerMethodField()
    artisan_nom = serializers.CharField(source='artisan.nom_entreprise', read_only=True)
    
    class Meta:
        model = Produit
        fields = [
            'id', 'nom', 'description', 'prix', 
            'categorie', 'disponible', 
            'date_creation', 'date_modification',
            'images', 'artisan', 'artisan_nom'
        ]
        read_only_fields = ['date_creation', 'date_modification', 'artisan']

    def get_categorie(self, obj):
        """Retourne l'objet catégorie complet"""
        if obj.categorie:
            return {
                'id': obj.categorie.id,
                'nom_categorie': obj.categorie.nom_categorie
            }
        return None


class ProduitCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour créer/modifier des produits avec upload d'images"""
    
    class Meta:
        model = Produit
        fields = [
            'id', 'nom', 'description', 'prix',
            'categorie', 'disponible'
        ]
        # ✅ IMPORTANT : Ne pas inclure 'artisan' ici car il est passé dans la vue

    def validate_prix(self, value):
        """Valide que le prix est positif"""
        if value <= 0:
            raise serializers.ValidationError("Le prix doit être supérieur à 0")
        return value

    def create(self, validated_data):
        """Crée un produit avec gestion des images"""
        request = self.context.get('request')
        
        # Crée le produit (l'artisan est passé via save(artisan=...))
        produit = Produit.objects.create(**validated_data)
        
        # ✅ CORRECTION : Gère les images APRÈS la création
        if request and hasattr(request, 'FILES'):
            print(f"DEBUG - FILES detected: {request.FILES.keys()}")
            self._handle_image_upload(produit, request.FILES)
        else:
            print("DEBUG - No FILES in request")
        
        return produit

    def update(self, instance, validated_data):
        """Met à jour un produit avec gestion des images"""
        request = self.context.get('request')
        
        # Met à jour les champs du produit
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Gère les nouvelles images si présentes
        if request and hasattr(request, 'FILES'):
            print(f"DEBUG - FILES detected in update: {request.FILES.keys()}")
            self._handle_image_upload(instance, request.FILES)
        
        return instance

    def _handle_image_upload(self, produit, files):
        """
        Gère l'upload des images
        Le frontend envoie les images avec des clés comme: images[0]image, images[1]image
        """
        print("=" * 60)
        print(f"🔍 DEBUG - Handling image upload pour produit ID: {produit.id}")
        print(f"📁 Files keys reçues: {list(files.keys())}")
        print(f"📁 Nombre de fichiers: {len(files)}")
        
        # Affiche les détails de chaque fichier
        for key, file in files.items():
            print(f"   - {key}: {file.name} ({file.size} bytes)")
        
        # Récupère l'ordre maximum actuel
        current_max_ordre = produit.images.count()
        print(f"📊 Ordre max actuel: {current_max_ordre}")
        
        # ✅ CORRECTION : Cherche toutes les clés qui contiennent 'image'
        image_keys = []
        for key in files.keys():
            if 'image' in key.lower():
                image_keys.append(key)
                print(f"   ✅ Clé valide trouvée: {key}")
        
        print(f"✅ Total: {len(image_keys)} image(s) à uploader")
        
        # Crée les images
        for index, key in enumerate(sorted(image_keys)):
            image_file = files[key]
            ordre = current_max_ordre + index
            print(f"📸 Création ImageProduit: {image_file.name} (ordre={ordre})")
            
            img = ImageProduit.objects.create(
                produit=produit,
                image=image_file,
                ordre=ordre
            )
            print(f"   ✅ ImageProduit créée avec ID: {img.id}, URL: {img.image.url}")
        
        final_count = produit.images.count()
        print(f"🎉 Total images pour produit {produit.id}: {final_count}")
        print("=" * 60)

    def to_representation(self, instance):
        """Utilise ProduitSerializer pour la réponse"""
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
        fields = [
            'id', 'nom_entreprise', 'logo', 'description',
            'categorie', 'rubrique', 'ville', 'pays',
            'actif', 'nombre_produits', 'has_location'
        ]

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
        fields = [
            'id', 'nom_entreprise', 'nom_proprietaire', 'description',
            'logo', 'categorie', 'rubrique', 'pays', 'ville', 'adresse',
            'localisation_latitude', 'localisation_longitude',
            'telephone', 'email', 'site_web', 'actif',
            'date_creation', 'date_modification',
            'produits', 'images', 'statistiques', 'has_location'
        ]


class ArtisanCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artisan
        fields = [
            'id',  # ← IMPORTANT : Retourne l'ID
            'uuid',  # ← Et l'UUID aussi
            'nom_entreprise', 'nom_proprietaire', 'description', 'logo',
            'categorie', 'rubrique', 'pays', 'ville', 'adresse',
            'telephone', 'email', 'actif'
        ]
        read_only_fields = ['id', 'uuid']  # ← Ces champs ne sont pas modifiables

    def validate_description(self, value):
        if len(value) < 50:
            raise serializers.ValidationError(
                "La description doit contenir au moins 50 caractères."
            )
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        if hasattr(user, 'artisan'):
            raise serializers.ValidationError(
                "Vous avez déjà un profil artisan."
            )
        artisan = Artisan.objects.create(user=user, **validated_data)
        StatistiqueArtisan.objects.create(artisan=artisan)
        return artisan


class LocationUpdateSerializer(serializers.Serializer):
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    adresse = serializers.CharField(max_length=300, required=False, allow_blank=True)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
