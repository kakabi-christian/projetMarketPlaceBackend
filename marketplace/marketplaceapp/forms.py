from django import forms
from .models import User
from .models import Activite, Specialite,PostComment,PostLike,Post,Artisan, ArtisanKYC
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
    
    




class PostCreationForm(forms.ModelForm):
        class Meta:
            model = Post
            fields = ['artisan', 'titre', 'description', 'media_url', 'media_type']
        
        def clean_media_url(self):
            media = self.cleaned_data.get('media_url')
            if media:
                # Vérifier la taille (max 10MB)
                if media.size > 10 * 1024 * 1024:
                    raise forms.ValidationError("La taille du fichier ne doit pas dépasser 10MB")
                
                # Vérifier le type de fichier
                media_type = self.cleaned_data.get('media_type')
                if media_type == 'IMAGE':
                    if not media.content_type.startswith('image/'):
                        raise forms.ValidationError("Le fichier doit être une image")
                elif media_type == 'VIDEO':
                    if not media.content_type.startswith('video/'):
                        raise forms.ValidationError("Le fichier doit être une vidéo")
            return media


class PostCommentForm(forms.ModelForm):
    """
    Formulaire pour permettre à un Utilisateur de commenter un Post.
    """
    commentaire = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Écrivez votre commentaire ici...',
            'rows': 3,
        }),
        label="Commentaire"
    )
    
    # post et user seront généralement passés au View/Serializer depuis l'URL ou la session/jeton
    # Nous les laissons ici pour ModelForm, mais les widgets ne sont pas nécessaires pour l'API.

    class Meta:
        model = PostComment
        fields = ['post', 'user', 'commentaire']

    

# Dans marketplaceapp/forms.py

class PostLikeForm(forms.ModelForm):
    class Meta:
        model = PostLike
        fields = ['post', 'user']
         


class ConversationForm(forms.ModelForm):
    """
    Formulaire pour créer une nouvelle conversation entre deux utilisateurs.
    L'API devra vérifier si une conversation user1-user2 ou user2-user1 existe déjà.
    """
    # user1 sera l'utilisateur courant (authentifié)
    # user2 sera l'artisan ou le client contacté
    
    class Meta:
        model = Conversation
        fields = ['user1', 'user2']
        # last_message est géré par le système après l'envoi du premier Message

    def clean(self):
        cleaned_data = super().clean()
        user1 = cleaned_data.get('user1')
        user2 = cleaned_data.get('user2')

        if user1 == user2:
            raise forms.ValidationError("Un utilisateur ne peut pas se parler à lui-même.")

        # Vérifier si une conversation existe déjà dans les deux sens
        exists = Conversation.objects.filter(
            (models.Q(user1=user1, user2=user2) | models.Q(user1=user2, user2=user1))
        ).exists()

        if exists:
        
            raise forms.ValidationError("Une conversation entre ces deux utilisateurs existe déjà.")

        return cleaned_data
    

# Dans marketplaceapp/forms.py

class MessageForm(forms.ModelForm):
    """
    Formulaire pour l'envoi d'un message dans une conversation existante.
    """
    contenu = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Tapez votre message...',
            'rows': 1,
        }),
        label="Contenu du message"
    )

    class Meta:
        model = Message
        fields = ['conversation', 'sender', 'contenu']

# Dans marketplaceapp/forms.py

class FeedbackForm(forms.ModelForm):
    """
    Formulaire pour soumettre un Feedback sur un Artisan (note et commentaire).
    Le modèle Feedback est lié à User et non Artisan. Vous devrez peut-être ajouter une 
    clé étrangère vers l'Artisan dans le modèle Feedback si c'est l'intention.
    Je suppose ici que le feedback est lié au User qui le donne, mais l'API devra 
    s'assurer que le feedback est bien *pour* un artisan spécifique.
    """
    # Si le feedback concerne un artisan, il faudrait ajouter:
    # artisan = forms.ModelChoiceField(queryset=Artisan.objects.all(), required=True)
    
    note = forms.IntegerField(
        min_value=1,
        max_value=5,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Note (1-5)'
        }),
        label="Note"
    )
    
    commentaire = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Votre avis (optionnel)',
            'rows': 3,
        }),
        required=False,
        label="Commentaire"
    )

    class Meta:
        model = Feedback
        fields = ['user', 'note', 'commentaire']


class SubscriptionForm(forms.ModelForm):
    """
    Formulaire pour s'abonner (suivre) un Artisan.
    """
    class Meta:
        model = Subscription
        fields = ['subscriber', 'artisan']
    
    def clean(self):
        cleaned_data = super().clean()
        subscriber = cleaned_data.get('subscriber')
        artisan = cleaned_data.get('artisan')

        if subscriber and artisan and subscriber.id == artisan.user_id:
            raise forms.ValidationError("Un artisan ne peut pas s'abonner à lui-même.")
            
        return cleaned_data



class ReportForm(forms.ModelForm):
    """
    Formulaire pour signaler un Post ou un Artisan.
    """
    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Décrivez la raison du signalement...',
            'rows': 4,
        }),
        label="Raison du signalement"
    )

    class Meta:
        model = Report
        fields = ['user', 'post', 'artisan', 'reason']
        # post et artisan sont tous les deux optionnels dans le modèle, 
        # mais l'un des deux doit être fourni pour que le rapport soit valide.

    def clean(self):
        cleaned_data = super().clean()
        post = cleaned_data.get('post')
        artisan = cleaned_data.get('artisan')
        
        if not post and not artisan:
            raise forms.ValidationError("Un rapport doit concerner soit un Post, soit un Artisan.")
            
        if post and artisan:
            raise forms.ValidationError("Un rapport ne peut pas concerner un Post et un Artisan simultanément.")
            
        return cleaned_data