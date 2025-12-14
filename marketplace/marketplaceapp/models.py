from decimal import Decimal
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
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

# models.py
from django.db import models

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
