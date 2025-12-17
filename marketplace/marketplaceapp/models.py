from decimal import Decimal
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid

User = get_user_model()

class Categorie(models.Model):
    nom_categorie = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    icone = models.CharField(max_length=50, blank=True, null=True)
    slug = models.SlugField(unique=True, blank=True)
    actif = models.BooleanField(default=True)
    ordre = models.IntegerField(default=0)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['ordre', 'nom_categorie']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nom_categorie)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nom_categorie


class Rubrique(models.Model):
    categorie = models.ForeignKey(
        Categorie,
        on_delete=models.CASCADE,
        related_name='rubriques'
    )
    nom_rubrique = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    slug = models.SlugField(blank=True)
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nom_rubrique']
        unique_together = ['categorie', 'nom_rubrique']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nom_rubrique)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.categorie.nom_categorie} - {self.nom_rubrique}"


class Artisan(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    nom_entreprise = models.CharField(max_length=200)
    nom_proprietaire = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True, max_length=250)
    description = models.TextField()
    logo = models.ImageField(
        upload_to='artisans/logos/%Y/%m/',
        blank=True,
        null=True
    )

    categorie = models.ForeignKey(
        Categorie,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='artisans'
    )
    rubrique = models.ForeignKey(
        Rubrique,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='artisans'
    )

    pays = models.CharField(max_length=100, default='Cameroun')
    ville = models.CharField(max_length=100)
    adresse = models.CharField(max_length=255, blank=True, null=True)
    localisation_latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    localisation_longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )

    telephone = models.CharField(max_length=20)
    email = models.EmailField()
    site_web = models.URLField(blank=True, null=True)

    horaires = models.JSONField(default=dict, blank=True)

    actif = models.BooleanField(default=True)
    certifie = models.BooleanField(default=False)
    premium = models.BooleanField(default=False)

    nombre_vues = models.PositiveIntegerField(default=0)
    nombre_favoris = models.PositiveIntegerField(default=0)
    note_moyenne = models.DecimalField(
        max_digits=3, decimal_places=2, default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    nombre_avis = models.PositiveIntegerField(default=0)

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_creation']

    @property
    def has_location(self):
        return self.localisation_latitude is not None and self.localisation_longitude is not None

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.nom_entreprise)
            slug = base_slug
            counter = 1
            while Artisan.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nom_entreprise} - {self.ville}"


class Produit(models.Model):
    """Modèle pour les produits/services des artisans"""
    artisan = models.ForeignKey(
        'Artisan', 
        on_delete=models.CASCADE, 
        related_name='produits'
    )
    nom = models.CharField(max_length=200)
    description = models.TextField()
    prix = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    categorie = models.ForeignKey(
        'Categorie', 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='produits'
    )
    disponible = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_creation']
        verbose_name = 'Produit'
        verbose_name_plural = 'Produits'

    def __str__(self):
        return f"{self.nom} - {self.artisan.nom_entreprise}"

    @property
    def prix_format(self):
        """Retourne le prix formaté"""
        return f"{self.prix:,.0f} FCFA"


class ImageProduit(models.Model):
    """Modèle pour les images des produits"""
    produit = models.ForeignKey(
        Produit, 
        on_delete=models.CASCADE, 
        related_name='images'
    )
    image = models.ImageField(upload_to='produits/%Y/%m/')
    ordre = models.IntegerField(default=0)
    date_ajout = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['ordre', 'date_ajout']
        verbose_name = 'Image de produit'
        verbose_name_plural = 'Images de produits'

    def __str__(self):
        return f"Image {self.ordre} - {self.produit.nom}"

    def delete(self, *args, **kwargs):
        """Supprime le fichier image lors de la suppression de l'objet"""
        if self.image:
            storage = self.image.storage
            if storage.exists(self.image.name):
                storage.delete(self.image.name)
        super().delete(*args, **kwargs)


class ArtisanImage(models.Model):
    artisan = models.ForeignKey(
        Artisan,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='artisans/images/%Y/%m/')
    type_image = models.CharField(max_length=50, default='galerie')
    date_upload = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_upload']

    def __str__(self):
        return f"Image {self.artisan.nom_entreprise}"


class StatistiqueArtisan(models.Model):
    artisan = models.OneToOneField(
        Artisan,
        on_delete=models.CASCADE,
        related_name='statistiques'
    )
    nombre_vues = models.PositiveIntegerField(default=0)
    nombre_favoris = models.PositiveIntegerField(default=0)
    derniere_mise_a_jour = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Stats {self.artisan.nom_entreprise}"


class UserProfile(models.Model):
    """Profil utilisateur avec rôle"""
    ROLE_CHOICES = [
        ('client', 'Client'),
        ('artisan', 'Artisan'),
        ('admin', 'Administrateur'),
    ]
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='profile'
    )
    role = models.CharField(
        max_length=10, 
        choices=ROLE_CHOICES, 
        default='client'
    )
    telephone = models.CharField(max_length=20, blank=True, null=True)
    photo = models.ImageField(
        upload_to='users/photos/', 
        blank=True, 
        null=True
    )
    date_naissance = models.DateField(blank=True, null=True)
    adresse = models.CharField(max_length=255, blank=True, null=True)
    ville = models.CharField(max_length=100, blank=True, null=True)
    pays = models.CharField(max_length=100, default='Cameroun')
    
    profile_artisan_complete = models.BooleanField(default=False)
    
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Profil Utilisateur'
        verbose_name_plural = 'Profils Utilisateurs'
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
    
    @property
    def is_artisan(self):
        return self.role == 'artisan'
    
    @property
    def is_client(self):
        return self.role == 'client'
    
    @property
    def is_admin(self):
        return self.role == 'admin'


class ProfilClient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='client_profile')
    
    # ✅ RELATION MANY-TO-MANY AVEC CATÉGORIES
    categories_preferees = models.ManyToManyField(
        'Categorie', 
        blank=True,
        related_name='clients_interesses'
    )
    
    ville_preference = models.CharField(max_length=100, blank=True)
    pays_preference = models.CharField(max_length=100, default='Cameroun')
    rayon_recherche_km = models.IntegerField(default=10)
    budget_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    budget_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    bio = models.TextField(blank=True)
    recevoir_nouveautes = models.BooleanField(default=True)
    recevoir_promotions = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    @property
    def nombre_favoris(self):
        return Favori.objects.filter(client=self.user).count()
    
# ✅ N'OUBLIEZ PAS le modèle Favori aussi :
class Favori(models.Model):
    """Système de favoris pour que les clients sauvegardent leurs artisans préférés"""
    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='mes_favoris'
    )
    artisan = models.ForeignKey(
        Artisan,
        on_delete=models.CASCADE,
        related_name='favoris_recus'
    )
    date_ajout = models.DateTimeField(auto_now_add=True)
    note_personnelle = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ['client', 'artisan']
        ordering = ['-date_ajout']
        verbose_name = 'Favori'
        verbose_name_plural = 'Favoris'
    
    def __str__(self):
        return f"{self.client.username} ♥ {self.artisan.nom_entreprise}"

class Conversation(models.Model):
    """Conversation entre un client et un artisan"""
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations_client')
    artisan = models.ForeignKey(Artisan, on_delete=models.CASCADE, related_name='conversations')
    date_creation = models.DateTimeField(auto_now_add=True)
    derniere_activite = models.DateTimeField(auto_now=True)
    
    # Statut de lecture
    client_non_lu = models.IntegerField(default=0)  # Nombre de messages non lus par le client
    artisan_non_lu = models.IntegerField(default=0)  # Nombre de messages non lus par l'artisan
    
    class Meta:
        unique_together = ('client', 'artisan')
        ordering = ['-derniere_activite']
    
    def __str__(self):
        return f"Conv: {self.client.username} <-> {self.artisan.nom_entreprise}"


class Message(models.Model):
    """Message dans une conversation"""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    expediteur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages_envoyes')
    contenu = models.TextField()
    date_envoi = models.DateTimeField(auto_now_add=True)
    lu = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['date_envoi']
    
    def __str__(self):
        return f"{self.expediteur.username}: {self.contenu[:50]}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Mettre à jour le compteur de non-lus
        conv = self.conversation
        if self.expediteur == conv.client:
            conv.artisan_non_lu += 1
        else:
            conv.client_non_lu += 1
        conv.derniere_activite = self.date_envoi
        conv.save()
