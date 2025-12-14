# marketplace/token_serializers.py

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Surcharge le sérialiseur JWT par défaut pour inclure l'ID de l'utilisateur
    sous la clé 'id' en plus de la clé 'user_id' par défaut.
    """
    @classmethod
    def get_token(cls, user):
        # Appel à la méthode parente pour obtenir le token de base
        token = super().get_token(user)

        # Ajout de l'ID de l'utilisateur sous la clé 'id'
        token['id'] = user.id
        
        # Si vous utilisez un modèle utilisateur personnalisé, assurez-vous que 'user' a bien un attribut 'id'
        
        return token