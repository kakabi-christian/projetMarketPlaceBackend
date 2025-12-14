# marketplace/token_claims.py

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Personnalise le token pour inclure l'ID de l'utilisateur sous la clé 'id'.
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Ajoutez ici les données personnalisées que vous voulez dans le payload du token
        token['id'] = user.id  # Assurez-vous que l'objet user a un attribut 'id'
        
        # Optionnel : ajouter l'email ou un autre champ utile
        # token['email'] = user.email

        return token