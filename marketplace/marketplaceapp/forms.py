from django import forms
from .models import User
from .models import Activite, Specialite
from .models import *


from django.contrib.auth.hashers import make_password, check_password  # <-- ajouter check_password

class ClientCreationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mot de passe'
        }),
        label="Mot de passe"
    )

    class Meta:
        model = User
        fields = [
            'nom',
            'prenom',
            'email',
            'telephone',
            'ville',
            'password'
        ]
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom'
            }),
            'prenom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Prénom'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email'
            }),
            'telephone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Téléphone'
            }),
            'ville': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ville'
            }),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        # 🔐 Hash du mot de passe
        user.password = make_password(self.cleaned_data['password'])
        # 🎯 Rôle par défaut = CLIENT
        user.role = 'CLIENT'
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email'
        }),
        label="Email"
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mot de passe'
        }),
        label="Mot de passe"
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        if not email or not password:
            raise forms.ValidationError("Email et mot de passe requis")

        try:
            user = User.objects.get(email=email, is_deleted=False)
        except User.DoesNotExist:
            raise forms.ValidationError("Email ou mot de passe incorrect")

        # 🔐 Vérification du mot de passe hashé
        if not check_password(password, user.password):
            raise forms.ValidationError("Email ou mot de passe incorrect")

        # 🔒 Vérification utilisateur actif
        if not user.is_active:
            raise forms.ValidationError("Compte désactivé")

        # ✅ Tout est OK → on stocke l'utilisateur
        cleaned_data['user'] = user
        return cleaned_data
class ActiviteForm(forms.ModelForm):
    class Meta:
        model = Activite
        fields = ['nom', 'description']
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom de l’activité'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Description (optionnelle)',
                'rows': 3,
            }),
        }


# Formulaire pour créer une spécialité
class SpecialiteForm(forms.ModelForm):
    class Meta:
        model = Specialite
        fields = ['activite', 'nom', 'description']
        widgets = {
            'activite': forms.Select(attrs={
                'class': 'form-control'
            }),
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom de la spécialité'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Description (optionnelle)',
                'rows': 3,
            }),
        }

class ArtisanCreationForm(forms.ModelForm):
    user = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True, is_deleted=False),
        widget=forms.Select(attrs={
            'class': 'form-control',
            'placeholder': 'Sélectionnez l’utilisateur'
        }),
        label="Utilisateur"
    )

    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Description de l’artisan',
            'rows': 4
        }),
        required=False,
        label="Description"
    )

    adresse = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Adresse de l’artisan'
        }),
        required=False,
        label="Adresse"
    )

    latitude = forms.FloatField(
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Latitude'
        }),
        required=False,
        label="Latitude"
    )

    longitude = forms.FloatField(
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Longitude'
        }),
        required=False,
        label="Longitude"
    )

    class Meta:
        model = Artisan
        fields = [
            'user',
            'description',
            'adresse',
            'latitude',
            'longitude',
        ]

    def save(self, commit=True):
        artisan = super().save(commit=False)
        # Vérification et valeurs par défaut
        if commit:
            artisan.save()
        return artisan
    


# ----------------------------------------------------
class ArtisanKYCForm(forms.ModelForm):
    # Champ Artisan (Clé Étrangère):
    # On utilise ModelChoiceField pour sélectionner l'Artisan auquel le KYC est associé.
    # Vous pouvez ajuster le queryset si nécessaire (par ex., filtrer les artisans sans KYC)
    artisan = forms.ModelChoiceField(
        queryset=Artisan.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-control',
            'placeholder': 'Artisan lié'
        }),
        label="Artisan"
    )

    # Champ photo_profil (ImageField):
    # Django utilise automatiquement FileInput/ClearableFileInput pour les champs de fichier/image.
    photo_profil = forms.ImageField(
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
        }),
        label="Photo de profil (Artisan)",
        help_text="Téléchargez une photo de profil."
    )

    # Champ cni (ImageField):
    cni = forms.ImageField(
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
        }),
        label="Pièce d'identité (CNI)",
        help_text="Téléchargez une photo/scan de votre CNI."
    )

    class Meta:
        model = ArtisanKYC
        fields = [
            'artisan', 
            'photo_profil', 
            'cni', 
            # Le statut, verified_by, verified_at, etc. ne sont pas inclus 
            # car ils sont gérés par le système (par défaut ou par un modérateur).
        ]