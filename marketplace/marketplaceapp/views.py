import json
from django.http import JsonResponse, Http404
from django.test import Client
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password, check_password
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.db.models import Q
from .models import Post, PostLike, PostComment
from .forms import PostCreationForm
# Importez vos modèles User, Artisan, ArtisanKYC, etc. ici
from .models import User, Artisan, ArtisanKYC, Activite, Specialite 
from .forms import ArtisanCreationForm, ArtisanKYCForm
from .models import Conversation, Message
from .models import Subscription, Report
from .models import PostLike
from .models import Notification

# ===================== AUTHENTIFICATION (API - Flutter) =====================

@csrf_exempt
def login(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

    try:
        data = json.loads(request.body)

        email = data.get('email')
        password = data.get('password')

        if not all([email, password]):
            return JsonResponse({'error': 'Email et mot de passe sont requis'}, status=400)

        try:
            user = User.objects.get(email=email, is_deleted=False)
        except User.DoesNotExist:
            return JsonResponse({'error': 'Email ou mot de passe incorrect'}, status=400)

        if not check_password(password, user.password):
            return JsonResponse({'error': 'Email ou mot de passe incorrect'}, status=400)

        if not user.is_active:
            return JsonResponse({'error': 'Compte désactivé'}, status=400)
            
        is_admin = (user.role == 'ADMIN')

        return JsonResponse({
            'success': True,
            'message': 'Connexion réussie',
            'user_id': user.id,
            'nom': user.nom,
            'prenom': user.prenom,
            'email': user.email,
            'telephone': user.telephone,
            'ville': user.ville,
            'role': user.role,
            'is_admin': is_admin,
            'is_verified': getattr(user, 'is_verified', False)
        }, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def register_client(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

    try:
        data = json.loads(request.body)

        nom = data.get('nom')
        prenom = data.get('prenom')
        email = data.get('email')
        password = data.get('password')
        telephone = data.get('telephone')
        ville = data.get('ville')

        if not all([nom, prenom, email, password]):
            return JsonResponse({'error': 'Champs obligatoires manquants'}, status=400)

        if User.objects.filter(email=email).exists():
            return JsonResponse({'error': 'Email déjà utilisé'}, status=400)

        user = User.objects.create(
            nom=nom,
            prenom=prenom,
            email=email,
            password=make_password(password),
            telephone=telephone,
            ville=ville,
            role='CLIENT'
        )

        return JsonResponse({
            'success': True,
            'message': 'Compte client créé avec succès',
            'user_id': user.id,
            'nom': user.nom,
            'prenom': user.prenom,
            'email': user.email,
            'telephone': user.telephone,
            'ville': user.ville,
            'role': user.role,
            'is_verified': getattr(user, 'is_verified', False)
        }, status=201)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ---------------------- Liste des clients ----------------------
@csrf_exempt
def list_clients(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

    try:
        clients = User.objects.filter(role='CLIENT')
        clients_list = [{
            'id': c.id,
            'nom': c.nom,
            'prenom': c.prenom,
            'email': c.email,
            'telephone': c.telephone,
            'ville': c.ville,
            'is_verified': getattr(c, 'is_verified', False)
        } for c in clients]
        return JsonResponse({'clients': clients_list}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ---------------------- Modification client ----------------------
@csrf_exempt
def update_client(request, client_id):
    if request.method != 'PUT':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

    try:
        client = User.objects.get(id=client_id, role='CLIENT')
        data = json.loads(request.body)

        client.nom = data.get('nom', client.nom)
        client.prenom = data.get('prenom', client.prenom)
        client.email = data.get('email', client.email)
        client.telephone = data.get('telephone', client.telephone)
        client.ville = data.get('ville', client.ville)

        if data.get('password'):
            client.password = make_password(data['password'])

        client.save()

        return JsonResponse({'success': True, 'message': 'Client mis à jour avec succès'}, status=200)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Client introuvable'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ---------------------- Suppression client ----------------------
@csrf_exempt
def delete_client(request, client_id):
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

    try:
        client = User.objects.get(id=client_id, role='CLIENT')
        client.delete()
        return JsonResponse({'success': True, 'message': 'Client supprimé avec succès'}, status=200)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Client introuvable'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q

# Assurez-vous d'importer vos modèles
from .models import User, Conversation, Message 
# Note : Vous aurez besoin de l'import make_password pour l'enregistrement, mais pas ici.


@csrf_exempt
def artisan_conversation_list(request, artisan_user_id):
    """
    [GET] Liste toutes les conversations où l'utilisateur spécifié (Artisan) est impliqué.
    Renvoie le client (l'interlocuteur) et le dernier message.
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
        
    try:
        # 1. Vérifier que l'utilisateur est un Artisan (bonne pratique de sécurité)
        artisan_user = User.objects.get(pk=artisan_user_id, is_deleted=False)
        if artisan_user.role != 'ARTISAN':
             return JsonResponse({'error': 'ID utilisateur non associé à un Artisan'}, status=403)
             
        # 2. Récupérer toutes les conversations de cet utilisateur
        conversations = Conversation.objects.filter(
            Q(user1=artisan_user) | Q(user2=artisan_user)
        ).select_related('user1', 'user2').order_by('-updated_at')
        
        conv_data = []
        for conv in conversations:
            # 3. Déterminer l'interlocuteur (le Client)
            # L'interlocuteur sera l'autre utilisateur dans la conversation
            client_user = conv.user1 if conv.user2 == artisan_user else conv.user2
            
            # (Optionnel, mais recommandé) Vérifier que l'interlocuteur est bien un CLIENT
            if client_user.role != 'CLIENT':
                continue # Ignore les conversations avec d'autres artisans/admins
            
            # 4. Compter les messages non lus (envoyés par le client)
            unread_count = Message.objects.filter(
                conversation=conv, 
                is_read=False
            ).exclude(sender=artisan_user).count()

            conv_data.append({
                'id': conv.id,
                'interlocuteur_id': client_user.id,
                'interlocuteur_nom': f"{client_user.nom} {client_user.prenom}",
                'interlocuteur_role': client_user.role,
                'last_message': conv.last_message,
                'updated_at': conv.updated_at.isoformat(),
                'unread_count': unread_count,
            })
            
        return JsonResponse({'success': True, 'conversations': conv_data}, status=200)

    except User.DoesNotExist:
        return JsonResponse({'error': 'Artisan non trouvé'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def register_artisan(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

    try:
        data = json.loads(request.body)

        nom = data.get('nom')
        prenom = data.get('prenom')
        email = data.get('email')
        password = data.get('password')
        telephone = data.get('telephone')
        ville = data.get('ville')

        if not all([nom, prenom, email, password]):
            return JsonResponse({'error': 'Champs obligatoires manquants'}, status=400)

        if User.objects.filter(email=email).exists():
            return JsonResponse({'error': 'Email déjà utilisé'}, status=400)

        user = User.objects.create(
            nom=nom,
            prenom=prenom,
            email=email,
            password=make_password(password),
            telephone=telephone,
            ville=ville,
            role='ARTISAN'
        )

        return JsonResponse({
            'success': True,
            'message': 'Compte artisan créé avec succès',
            'user_id': user.id,
            'nom': user.nom,
            'prenom': user.prenom,
            'email': user.email,
            'telephone': user.telephone,
            'ville': user.ville,
            'role': user.role,
            'is_verified': getattr(user, 'is_verified', False)
        }, status=201)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===================== ACTIVITE =====================

@csrf_exempt
def activite_create(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    try:
        data = json.loads(request.body)
        nom = data.get('nom')
        description = data.get('description', '')

        if not nom:
            return JsonResponse({'error': 'Le nom est requis'}, status=400)

        activite = Activite.objects.create(nom=nom, description=description)
        return JsonResponse({
            'success': True,
            'message': 'Activité créée avec succès',
            'id': activite.id,
            'nom': activite.nom,
            'description': activite.description
        }, status=201)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def activite_list(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    try:
        activites = list(Activite.objects.values())
        return JsonResponse({'activites': activites}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def activite_update(request, activite_id):
    if request.method != 'PUT':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    try:
        activite = Activite.objects.get(id=activite_id)
        data = json.loads(request.body)
        activite.nom = data.get('nom', activite.nom)
        activite.description = data.get('description', activite.description)
        activite.save()
        return JsonResponse({'success': True, 'message': 'Activité mise à jour'})
    except Activite.DoesNotExist:
        return JsonResponse({'error': 'Activité non trouvée'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def activite_delete(request, activite_id):
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    try:
        activite = Activite.objects.get(id=activite_id)
        activite.delete()
        return JsonResponse({'success': True, 'message': 'Activité supprimée'})
    except Activite.DoesNotExist:
        return JsonResponse({'error': 'Activité non trouvée'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ===================== SPECIALITE =====================

@csrf_exempt
def specialite_create(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    try:
        data = json.loads(request.body)
        nom = data.get('nom')
        description = data.get('description', '')
        activite_id = data.get('activite_id')

        if not nom or not activite_id:
            return JsonResponse({'error': 'Nom et activite_id requis'}, status=400)

        specialite = Specialite.objects.create(
            nom=nom,
            description=description,
            activite_id=activite_id
        )
        return JsonResponse({
            'success': True,
            'message': 'Spécialité créée avec succès',
            'id': specialite.id,
            'nom': specialite.nom,
            'description': specialite.description,
            'activite_id': specialite.activite_id
        }, status=201)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def specialite_list(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    try:
        specialites = list(Specialite.objects.values())
        return JsonResponse({'specialites': specialites}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def specialite_update(request, specialite_id):
    if request.method != 'PUT':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    try:
        specialite = Specialite.objects.get(id=specialite_id)
        data = json.loads(request.body)
        specialite.nom = data.get('nom', specialite.nom)
        specialite.description = data.get('description', specialite.description)
        if data.get('activite_id'):
            specialite.activite_id = data['activite_id']
        specialite.save()
        return JsonResponse({'success': True, 'message': 'Spécialité mise à jour'})
    except Specialite.DoesNotExist:
        return JsonResponse({'error': 'Spécialité non trouvée'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def specialite_delete(request, specialite_id):
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    try:
        specialite = Specialite.objects.get(id=specialite_id)
        specialite.delete()
        return JsonResponse({'success': True, 'message': 'Spécialité supprimée'})
    except Specialite.DoesNotExist:
        return JsonResponse({'error': 'Spécialité non trouvée'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ===================== ARTISAN =====================

@csrf_exempt
def artisan_create(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    try:
        data = json.loads(request.body)
        form = ArtisanCreationForm(data)
        if form.is_valid():
            artisan = form.save()
            return JsonResponse({
                'success': True,
                'message': 'Artisan créé avec succès',
                'id': artisan.id,
                'user_id': artisan.user_id,
                'description': artisan.description,
                'adresse': artisan.adresse,
                'latitude': artisan.latitude,
                'longitude': artisan.longitude,
                'is_verified': artisan.is_verified
            }, status=201)
        else:
            return JsonResponse({'error': form.errors}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def artisan_list(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    try:
        # Récupérer les artisans avec les informations de l'utilisateur associé
        artisans = Artisan.objects.filter(is_deleted=False).select_related('user')
        
        artisans_data = []
        for artisan in artisans:
            artisan_dict = {
                'id': artisan.id,
                'user_id': artisan.user.id,
                'nom': artisan.user.nom,  # 👈 Ajout du nom
                'prenom': artisan.user.prenom,  # 👈 Ajout du prénom
                'email': artisan.user.email,
                'telephone': artisan.user.telephone,
                'ville': artisan.user.ville,
                'description': artisan.description,
                'adresse': artisan.adresse,
                'latitude': artisan.latitude,
                'longitude': artisan.longitude,
                'is_verified': artisan.is_verified,
                'verified_at': artisan.verified_at.isoformat() if artisan.verified_at else None,
                'created_at': artisan.created_at.isoformat(),
                'updated_at': artisan.updated_at.isoformat(),
            }
            artisans_data.append(artisan_dict)
        
        return JsonResponse({'artisans': artisans_data}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def artisan_update(request, artisan_id):
    if request.method != 'PUT':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    try:
        artisan = Artisan.objects.get(id=artisan_id)
        data = json.loads(request.body)
        form = ArtisanCreationForm(data, instance=artisan)
        if form.is_valid():
            artisan = form.save()
            return JsonResponse({'success': True, 'message': 'Artisan mis à jour'})
        else:
            return JsonResponse({'error': form.errors}, status=400)
    except Artisan.DoesNotExist:
        return JsonResponse({'error': 'Artisan non trouvé'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def artisan_delete(request, artisan_id):
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    try:
        artisan = Artisan.objects.get(id=artisan_id)
        artisan.is_deleted = True
        artisan.save()
        return JsonResponse({'success': True, 'message': 'Artisan marqué comme supprimé'})
    except Artisan.DoesNotExist:
        return JsonResponse({'error': 'Artisan non trouvé'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ===================== ARTISAN KYC (API) =====================

@csrf_exempt
def artisan_kyc_submit(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    try:
        artisan_id = request.POST.get('artisan')

        if not artisan_id:
            return JsonResponse({'error': 'L\'ID de l\'artisan est requis.'}, status=400)

        try:
            artisan = Artisan.objects.get(pk=artisan_id)
        except Artisan.DoesNotExist:
            return JsonResponse({'error': 'Artisan non trouvé.'}, status=404)
            
        if ArtisanKYC.objects.filter(artisan=artisan).exists():
            return JsonResponse({'error': 'Les documents KYC pour cet artisan ont déjà été soumis.'}, status=400)

        form = ArtisanKYCForm(request.POST, request.FILES)

        if form.is_valid():
            kyc = form.save(commit=False)
            kyc.artisan = artisan
            kyc.save() 
            
            return JsonResponse({
                'success': True,
                'message': 'Documents KYC soumis avec succès. En attente de vérification.',
                'kyc_id': kyc.id,
                'artisan_id': kyc.artisan_id,
                'statut': kyc.statut,
            }, status=201)
        else:
            return JsonResponse({'error': 'Erreur de validation des données', 'details': form.errors}, status=400)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ================== ADMIN/WEB - AUTHENTIFICATION ET NAVIGATION ==================

@csrf_exempt
def admin_login(request):
    # 1. Vérifier si l'utilisateur est déjà connecté via la session
    if request.session.get('user_id'):
        try:
            user = User.objects.get(id=request.session['user_id'], is_deleted=False)
            if user.role == 'ADMIN':
                return redirect('admin_dashboard')
        except User.DoesNotExist:
            request.session.flush()

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        if not all([email, password]):
            error_message = "Veuillez entrer l'email et le mot de passe."
            return render(request, 'admin_dashboard/login.html', {'error': error_message})

        try:
            user = User.objects.get(email__iexact=email, is_deleted=False)
        except User.DoesNotExist:
            error_message = "Email ou mot de passe incorrect."
            return render(request, 'admin_dashboard/login.html', {'error': error_message})

        if check_password(password, user.password):
            if user.role == 'ADMIN':
                # Créer la session manuellement
                request.session['user_id'] = user.id
                request.session['user_email'] = user.email
                request.session['user_nom'] = user.nom
                request.session['user_prenom'] = user.prenom
                request.session['user_role'] = user.role
                
                # Pas de messages, redirection directe
                return redirect('admin_dashboard')
            else:
                error_message = "Accès non autorisé. Vous n'êtes pas un administrateur."
                return render(request, 'admin_dashboard/login.html', {'error': error_message})
        else:
            error_message = "Email ou mot de passe incorrect."
            return render(request, 'admin_dashboard/login.html', {'error': error_message})

    return render(request, 'admin_dashboard/login.html')


def admin_dashboard(request):
    user_id = request.session.get('user_id')
    
    if not user_id:
        return redirect('admin_login')
    
    try:
        user = User.objects.get(id=user_id, is_deleted=False)
        if user.role != 'ADMIN':
            return redirect('admin_login')
    except User.DoesNotExist:
        request.session.flush()
        return redirect('admin_login')
    
    kyc_pending_count = ArtisanKYC.objects.filter(statut='PENDING').count()
    total_artisans = Artisan.objects.filter(is_deleted=False).count()
    
    context = {
        'kyc_pending_count': kyc_pending_count,
        'total_artisans': total_artisans,
        'user': user,
    }
    return render(request, 'admin_dashboard/dashboard.html', context)


def admin_logout(request):
    request.session.flush()
    return redirect('admin_login')


# ================== ADMIN/WEB - GESTION KYC ==================

def kyc_list(request):
    user_id = request.session.get('user_id')
    
    if not user_id:
        return redirect('admin_login')
    
    try:
        user = User.objects.get(id=user_id, is_deleted=False)
        if user.role != 'ADMIN':
            return redirect('admin_login')
    except User.DoesNotExist:
        request.session.flush()
        return redirect('admin_login')
    
    kyc_to_review = ArtisanKYC.objects.filter(
        statut__in=['PENDING', 'REJECTED']
    ).select_related('artisan__user').order_by('-created_at')
    
    context = {
        'kyc_to_review': kyc_to_review,
        'user': user,
    }
    return render(request, 'admin_dashboard/kyc_list.html', context)


def kyc_detail(request, kyc_id):
    user_id = request.session.get('user_id')
    
    if not user_id:
        return redirect('admin_login')
    
    try:
        user = User.objects.get(id=user_id, is_deleted=False)
        if user.role != 'ADMIN':
            return redirect('admin_login')
    except User.DoesNotExist:
        request.session.flush()
        return redirect('admin_login')

    kyc = get_object_or_404(ArtisanKYC.objects.select_related('artisan__user'), pk=kyc_id)
    
    context = {
        'kyc': kyc,
        'artisan': kyc.artisan,
        'artisan_user': kyc.artisan.user,
        'photo_profil_url': kyc.photo_profil.url if kyc.photo_profil else None,
        'cni_url': kyc.cni.url if kyc.cni else None,
        'user': user,
    }
    return render(request, 'admin_dashboard/kyc_detail.html', context)


def kyc_validate(request, kyc_id):
    user_id = request.session.get('user_id')
    
    if not user_id or request.method != 'POST':
        return redirect('admin_login')
    
    try:
        user = User.objects.get(id=user_id, is_deleted=False)
        if user.role != 'ADMIN':
            return redirect('admin_login')
    except User.DoesNotExist:
        request.session.flush()
        return redirect('admin_login')

    kyc = get_object_or_404(ArtisanKYC, pk=kyc_id)
    
    if kyc.statut != 'APPROVED':
        kyc.statut = 'APPROVED'
        kyc.verified_by = user
        kyc.verified_at = timezone.now()
        kyc.save()
        
        artisan = kyc.artisan
        artisan.is_verified = True
        artisan.verified_at = timezone.now()
        artisan.save()
        
    return redirect('kyc_list')


def kyc_reject(request, kyc_id):
    user_id = request.session.get('user_id')
    
    if not user_id or request.method != 'POST':
        return redirect('admin_login')
    
    try:
        user = User.objects.get(id=user_id, is_deleted=False)
        if user.role != 'ADMIN':
            return redirect('admin_login')
    except User.DoesNotExist:
        request.session.flush()
        return redirect('admin_login')

    kyc = get_object_or_404(ArtisanKYC, pk=kyc_id)
    
    if kyc.statut != 'REJECTED':
        kyc.statut = 'REJECTED'
        kyc.verified_by = user
        kyc.verified_at = timezone.now()
        kyc.save()
        
        artisan = kyc.artisan
        artisan.is_verified = False
        artisan.save()
        
    return redirect('kyc_list')

# ===================== POSTS (API) =====================

@csrf_exempt
def post_create(request):
    """
    Créer un nouveau post (artisan uniquement)
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    try:
        # Récupérer l'artisan_id depuis le corps de la requête
        artisan_id = request.POST.get('artisan_id')
        
        if not artisan_id:
            return JsonResponse({'error': 'L\'ID de l\'artisan est requis'}, status=400)
        
        # Vérifier que l'artisan existe
        try:
            artisan = Artisan.objects.get(pk=artisan_id, is_deleted=False)
        except Artisan.DoesNotExist:
            return JsonResponse({'error': 'Artisan non trouvé'}, status=404)
        
        # Créer le post
        titre = request.POST.get('titre')
        description = request.POST.get('description', '')
        media_url = request.FILES.get('media_url')
        media_type = request.POST.get('media_type', 'IMAGE')
        
        if not titre:
            return JsonResponse({'error': 'Le titre est requis'}, status=400)
        
        if not media_url:
            return JsonResponse({'error': 'Le média est requis'}, status=400)
        
        # Calculer la taille du fichier
        media_size = media_url.size / (1024 * 1024)  # Taille en MB
        
        # Créer le post
        post = Post.objects.create(
            artisan=artisan,
            titre=titre,
            description=description,
            media_url=media_url,
            media_type=media_type,
            media_size=media_size,
            media_mime=media_url.content_type
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Post créé avec succès',
            'post': {
                'id': post.id,
                'titre': post.titre,
                'description': post.description,
                'media_url': request.build_absolute_uri(post.media_url.url),
                'media_type': post.media_type,
                'likes_count': post.likes_count,
                'comments_count': post.comments_count,
                'created_at': post.created_at.isoformat(),
            }
        }, status=201)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def post_list(request):
    """
    Lister tous les posts (avec pagination optionnelle)
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    try:
        # Récupérer tous les posts non supprimés
        posts = Post.objects.filter(is_deleted=False).select_related(
            'artisan__user'
        ).order_by('-created_at')
        
        # Pagination optionnelle
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        
        start = (page - 1) * page_size
        end = start + page_size
        
        posts_data = []
        for post in posts[start:end]:
            posts_data.append({
                'id': post.id,
                'titre': post.titre,
                'description': post.description,
                'media_url': request.build_absolute_uri(post.media_url.url) if post.media_url else None,
                'media_type': post.media_type,
                'likes_count': post.likes_count,
                'comments_count': post.comments_count,
                'created_at': post.created_at.isoformat(),
                'artisan': {
                    'id': post.artisan.id,
                    'nom': post.artisan.user.nom,
                    'prenom': post.artisan.user.prenom,
                    'is_verified': post.artisan.is_verified,
                }
            })
        
        return JsonResponse({
            'success': True,
            'posts': posts_data,
            'page': page,
            'page_size': page_size,
            'total': posts.count()
        }, status=200)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def post_detail(request, post_id):
    """
    Récupérer les détails d'un post
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    try:
        post = Post.objects.select_related('artisan__user').get(
            pk=post_id, 
            is_deleted=False
        )
        
        return JsonResponse({
            'success': True,
            'post': {
                'id': post.id,
                'titre': post.titre,
                'description': post.description,
                'media_url': request.build_absolute_uri(post.media_url.url) if post.media_url else None,
                'media_type': post.media_type,
                'media_size': post.media_size,
                'likes_count': post.likes_count,
                'comments_count': post.comments_count,
                'created_at': post.created_at.isoformat(),
                'artisan': {
                    'id': post.artisan.id,
                    'nom': post.artisan.user.nom,
                    'prenom': post.artisan.user.prenom,
                    'email': post.artisan.user.email,
                    'is_verified': post.artisan.is_verified,
                }
            }
        }, status=200)
        
    except Post.DoesNotExist:
        return JsonResponse({'error': 'Post non trouvé'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def post_delete(request, post_id):
    """
    Supprimer un post (soft delete)
    """
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    try:
        post = Post.objects.get(pk=post_id)
        post.is_deleted = True
        post.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Post supprimé avec succès'
        }, status=200)
        
    except Post.DoesNotExist:
        return JsonResponse({'error': 'Post non trouvé'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



@csrf_exempt
def artisan_posts(request, artisan_id):
    """
    Récupère tous les posts d'un artisan spécifique
    GET /api/artisan/<artisan_id>/posts/
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    try:
        # Vérifier que l'artisan existe
        artisan = Artisan.objects.filter(id=artisan_id, is_deleted=False).first()
        if not artisan:
            return JsonResponse({'error': 'Artisan non trouvé'}, status=404)
        
        # Récupérer les posts de l'artisan (non supprimés)
        posts = Post.objects.filter(
            artisan_id=artisan_id,
            is_deleted=False
        ).select_related('artisan__user').order_by('-created_at')
        
        # Construire la liste des posts
        posts_data = []
        for post in posts:
            post_dict = {
                'id': post.id,
                'artisan_id': post.artisan.id,
                'artisan_user_id': post.artisan.user.id,
                'artisan_nom': post.artisan.user.nom,
                'artisan_prenom': post.artisan.user.prenom,
                'artisan_is_verified': post.artisan.is_verified,
                'titre': post.titre,
                'description': post.description,
                'media_url': post.media_url,
                'likes_count': post.likes_count,
                'comments_count': post.comments_count,
                'created_at': post.created_at.isoformat(),
                'updated_at': post.updated_at.isoformat(),
            }
            posts_data.append(post_dict)
        
        return JsonResponse({
            'success': True,
            'artisan': {
                'id': artisan.id,
                'nom': artisan.user.nom,
                'prenom': artisan.user.prenom,
                'description': artisan.description,
            },
            'posts_count': len(posts_data),
            'posts': posts_data
        }, status=200)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def user_artisan_posts(request, user_id):
    """
    Récupère tous les posts d'un artisan à partir de son user_id
    GET /api/user/<user_id>/posts/
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    try:
        # Récupérer l'artisan associé à cet utilisateur
        artisan = Artisan.objects.filter(
            user_id=user_id,
            is_deleted=False
        ).first()
        
        if not artisan:
            return JsonResponse({
                'error': 'Aucun artisan trouvé pour cet utilisateur'
            }, status=404)
        
        # Récupérer les posts de l'artisan
        posts = Post.objects.filter(
            artisan=artisan,
            is_deleted=False
        ).select_related('artisan__user').order_by('-created_at')
        
        posts_data = []
        for post in posts:
            post_dict = {
                'id': post.id,
                'artisan_id': post.artisan.id,
                'artisan_user_id': post.artisan.user.id,
                'artisan_nom': post.artisan.user.nom,
                'artisan_prenom': post.artisan.user.prenom,
                'artisan_is_verified': post.artisan.is_verified,
                'titre': post.titre,
                'description': post.description,
                'media_url': post.media_url,
                'likes_count': post.likes_count,
                'comments_count': post.comments_count,
                'created_at': post.created_at.isoformat(),
                'updated_at': post.updated_at.isoformat(),
            }
            posts_data.append(post_dict)
        
        return JsonResponse({
            'success': True,
            'artisan': {
                'id': artisan.id,
                'user_id': artisan.user.id,
                'nom': artisan.user.nom,
                'prenom': artisan.user.prenom,
                'description': artisan.description,
                'is_verified': artisan.is_verified,
            },
            'posts_count': len(posts_data),
            'posts': posts_data
        }, status=200)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
@csrf_exempt
def post_like(request, post_id):
    """
    Liker/Unliker un post
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        
        if not user_id:
            return JsonResponse({'error': 'L\'ID de l\'utilisateur est requis'}, status=400)
        
        post = Post.objects.get(pk=post_id, is_deleted=False)
        user = User.objects.get(pk=user_id)
        
        # Vérifier si l'utilisateur a déjà liké
        like = PostLike.objects.filter(post=post, user=user).first()
        
        if like:
            # Unliker
            like.delete()
            post.likes_count -= 1
            post.save()
            message = 'Like retiré'
            liked = False
        else:
            # Liker
            PostLike.objects.create(post=post, user=user)
            post.likes_count += 1
            post.save()
            message = 'Post liké'
            liked = True
        
        return JsonResponse({
            'success': True,
            'message': message,
            'liked': liked,
            'likes_count': post.likes_count
        }, status=200)
        
    except Post.DoesNotExist:
        return JsonResponse({'error': 'Post non trouvé'}, status=404)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Utilisateur non trouvé'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ===================== POST COMMENTS (API) =====================

@csrf_exempt
def post_comment_create(request, post_id):
    """
    Ajouter un commentaire à un post.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        commentaire_text = data.get('commentaire')
        
        if not all([user_id, commentaire_text]):
            return JsonResponse({'error': 'ID utilisateur et commentaire sont requis'}, status=400)
            
        post = Post.objects.get(pk=post_id, is_deleted=False)
        user = User.objects.get(pk=user_id, is_deleted=False)
        
        # Création du commentaire
        comment = PostComment.objects.create(
            post=post,
            user=user,
            commentaire=commentaire_text
        )
        
        # Mise à jour du compteur de commentaires du Post
        post.comments_count += 1
        post.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Commentaire ajouté avec succès',
            'comment': {
                'id': comment.id,
                'user_id': user.id,
                'user_name': f"{user.nom} {user.prenom}",
                'commentaire': comment.commentaire,
                'created_at': comment.created_at.isoformat(),
            },
            'comments_count': post.comments_count
        }, status=201)
        
    except Post.DoesNotExist:
        return JsonResponse({'error': 'Post non trouvé'}, status=404)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Utilisateur non trouvé'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def post_comment_list(request, post_id):
    """
    Lister les commentaires d'un post.
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
        
    try:
        post = Post.objects.get(pk=post_id, is_deleted=False)
        comments = PostComment.objects.filter(
            post=post, 
            is_deleted=False
        ).select_related('user').order_by('created_at')
        
        comments_data = []
        for comment in comments:
            comments_data.append({
                'id': comment.id,
                'user_id': comment.user.id,
                'user_name': f"{comment.user.nom} {comment.user.prenom}",
                'commentaire': comment.commentaire,
                'created_at': comment.created_at.isoformat(),
            })
            
        return JsonResponse({
            'success': True,
            'comments': comments_data,
            'total': len(comments_data)
        }, status=200)

    except Post.DoesNotExist:
        return JsonResponse({'error': 'Post non trouvé'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===================== MESSAGERIE (API) =====================

@csrf_exempt
def conversation_list(request, user_id):
    """
    Lister toutes les conversations d'un utilisateur.
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
        
    try:
        user = User.objects.get(pk=user_id, is_deleted=False)
        conversations = Conversation.objects.filter(
            Q(user1=user) | Q(user2=user)
        ).select_related('user1', 'user2').order_by('-updated_at')
        
        conv_data = []
        for conv in conversations:
            # Déterminer l'interlocuteur
            other_user = conv.user1 if conv.user2 == user else conv.user2
            
            # Compter les messages non lus (si l'utilisateur courant est le destinataire)
            unread_count = Message.objects.filter(
                conversation=conv, 
                is_read=False
            ).exclude(sender=user).count()

            conv_data.append({
                'id': conv.id,
                'interlocuteur_id': other_user.id,
                'interlocuteur_nom': f"{other_user.nom} {other_user.prenom}",
                'last_message': conv.last_message,
                'updated_at': conv.updated_at.isoformat(),
                'unread_count': unread_count,
            })
            
        return JsonResponse({'success': True, 'conversations': conv_data}, status=200)

    except User.DoesNotExist:
        return JsonResponse({'error': 'Utilisateur non trouvé'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def conversation_detail_or_create(request):
    """
    GET: Récupérer ou Créer une conversation entre deux utilisateurs.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
        
    try:
        data = json.loads(request.body)
        user1_id = data.get('user1_id') # L'utilisateur courant
        user2_id = data.get('user2_id') # L'interlocuteur
        
        if not all([user1_id, user2_id]):
            return JsonResponse({'error': 'Les ID des deux utilisateurs sont requis'}, status=400)
            
        user1 = User.objects.get(pk=user1_id, is_deleted=False)
        user2 = User.objects.get(pk=user2_id, is_deleted=False)
        
        if user1 == user2:
            return JsonResponse({'error': 'Impossible de démarrer une conversation avec soi-même'}, status=400)
            
        # Tenter de trouver une conversation existante (dans les deux sens)
        conv = Conversation.objects.filter(
            Q(user1=user1, user2=user2) | Q(user1=user2, user2=user1)
        ).first()

        if not conv:
            # Créer une nouvelle conversation
            conv = Conversation.objects.create(user1=user1, user2=user2, last_message="")
            
        return JsonResponse({
            'success': True,
            'message': 'Conversation récupérée ou créée',
            'conversation_id': conv.id,
            'user1_id': user1.id,
            'user2_id': user2.id,
        }, status=200)

    except User.DoesNotExist:
        return JsonResponse({'error': 'Un des utilisateurs n\'a pas été trouvé'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# Correction de la fonction message_list dans views.py

@csrf_exempt
def message_list(request, conv_id): 
    """
    Lister tous les messages d'une conversation et marquer les messages comme lus.
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
        
    try:
        # Récupération de l'ID utilisateur via query parameter
        user_id_str = request.GET.get('user_id')
        if not user_id_str:
             return JsonResponse({'error': 'Le paramètre user_id est manquant'}, status=400)
             
        user_id = int(user_id_str)
        
        conv = Conversation.objects.get(pk=conv_id)
        user = User.objects.get(pk=user_id, is_deleted=False) 
        
        # Vérification d'accès...
        if user != conv.user1 and user != conv.user2:
            return JsonResponse({'error': 'Accès non autorisé à cette conversation'}, status=403)

        # 1. Récupération des messages
        messages = Message.objects.filter(
            conversation=conv, 
            is_deleted=False
        ).select_related('sender').order_by('created_at')
        
        messages_data = []
        
        # 🎯 CORRECTION: INITIALISER LA LISTE ICI !
        message_ids_to_mark_as_read = [] 

        # 2. Sérialisation et Identification des messages à lire
        for msg in messages:
            messages_data.append({
                'id': msg.id,
                'sender_id': msg.sender.id,
                'sender_name': f"{msg.sender.nom} {msg.sender.prenom}",
                'contenu': msg.contenu,
                'is_read': msg.is_read,
                'created_at': msg.created_at.isoformat(),
            })
            
            # Si l'utilisateur courant est le destinataire et que le message n'est pas lu
            if msg.sender != user and not msg.is_read:
                message_ids_to_mark_as_read.append(msg.id)
                
        # 3. Marquer les messages comme lus en masse
        if message_ids_to_mark_as_read: # Vérification optionnelle pour éviter une requête inutile
            Message.objects.filter(id__in=message_ids_to_mark_as_read).update(is_read=True)

        return JsonResponse({'success': True, 'messages': messages_data}, status=200)

    except Conversation.DoesNotExist:
        return JsonResponse({'error': 'Conversation non trouvée'}, status=404)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Utilisateur non trouvé'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def message_send(request, conv_id):
    """
    Envoyer un message dans une conversation.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
        
    try:
        data = json.loads(request.body)
        sender_id = data.get('sender_id')
        contenu = data.get('contenu')
        
        if not all([sender_id, contenu]):
            return JsonResponse({'error': 'ID de l\'expéditeur et contenu sont requis'}, status=400)
            
        conv = Conversation.objects.get(pk=conv_id)
        sender = User.objects.get(pk=sender_id, is_deleted=False)
        
        # Vérifier que l'expéditeur fait partie de la conversation
        if sender != conv.user1 and sender != conv.user2:
            return JsonResponse({'error': 'Accès non autorisé à cette conversation'}, status=403)

        # Création du message
        message = Message.objects.create(
            conversation=conv,
            sender=sender,
            contenu=contenu
        )
        
        # Mise à jour de la dernière activité de la conversation
        conv.last_message = contenu
        conv.updated_at = timezone.now()
        conv.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Message envoyé',
            'message_id': message.id
        }, status=201)

    except Conversation.DoesNotExist:
        return JsonResponse({'error': 'Conversation non trouvée'}, status=404)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Expéditeur non trouvé'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    


# ===================== ABONNEMENT (API) =====================

@csrf_exempt
def toggle_subscription(request):
    """
    S'abonner ou se désabonner d'un artisan.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
        
    try:
        data = json.loads(request.body)
        subscriber_id = data.get('subscriber_id')
        artisan_id = data.get('artisan_id')
        
        if not all([subscriber_id, artisan_id]):
            return JsonResponse({'error': 'IDs de l\'abonné et de l\'artisan requis'}, status=400)
            
        subscriber = User.objects.get(pk=subscriber_id, is_deleted=False)
        artisan = Artisan.objects.get(pk=artisan_id, is_deleted=False)
        
        subscription = Subscription.objects.filter(subscriber=subscriber, artisan=artisan).first()
        
        if subscription:
            # Désabonnement
            subscription.delete()
            message = 'Abonnement retiré'
            is_subscribed = False
        else:
            # Abonnement
            if subscriber.id == artisan.user_id:
                return JsonResponse({'error': 'Un artisan ne peut pas s\'abonner à lui-même'}, status=400)
                
            Subscription.objects.create(subscriber=subscriber, artisan=artisan)
            message = 'Abonnement réussi'
            is_subscribed = True
            
        return JsonResponse({
            'success': True,
            'message': message,
            'is_subscribed': is_subscribed,
        }, status=200)

    except User.DoesNotExist:
        return JsonResponse({'error': 'Abonné non trouvé'}, status=404)
    except Artisan.DoesNotExist:
        return JsonResponse({'error': 'Artisan non trouvé'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ===================== REPORTING (API) =====================

@csrf_exempt
def report_create(request):
    """
    Créer un nouveau rapport (signalement de post ou d'artisan).
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
        
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        post_id = data.get('post_id') # Optionnel
        artisan_id = data.get('artisan_id') # Optionnel
        reason = data.get('reason')
        
        if not all([user_id, reason]):
            return JsonResponse({'error': 'ID utilisateur et raison du rapport requis'}, status=400)
            
        if not post_id and not artisan_id:
            return JsonResponse({'error': 'Le rapport doit cibler un Post ou un Artisan'}, status=400)
            
        user = User.objects.get(pk=user_id, is_deleted=False)
        post = Post.objects.get(pk=post_id, is_deleted=False) if post_id else None
        artisan = Artisan.objects.get(pk=artisan_id, is_deleted=False) if artisan_id else None
        
        if post and artisan:
            return JsonResponse({'error': 'Le rapport ne peut cibler qu\'un seul élément'}, status=400)
            
        report = Report.objects.create(
            user=user,
            post=post,
            artisan=artisan,
            reason=reason,
            status='PENDING'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Rapport soumis avec succès. Il sera examiné.',
            'report_id': report.id,
            'status': report.status
        }, status=201)

    except User.DoesNotExist:
        return JsonResponse({'error': 'Utilisateur non trouvé'}, status=404)
    except Post.DoesNotExist:
        return JsonResponse({'error': 'Post ciblé non trouvé'}, status=404)
    except Artisan.DoesNotExist:
        return JsonResponse({'error': 'Artisan ciblé non trouvé'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def stats_dashboard(request):
    data = {

        # =====================
        # USERS
        # =====================
        "users": {
            "total": User.objects.count(),
            "admins": User.objects.filter(role='ADMIN').count(),
            "artisans": User.objects.filter(role='ARTISAN').count(),
            "clients": User.objects.filter(role='CLIENT').count(),
            "active": User.objects.filter(is_active=True).count(),
            "deleted": User.objects.filter(is_deleted=True).count(),
        },

        # =====================
        # ARTISANS
        # =====================
        "artisans": {
            "total": Artisan.objects.count(),
            "verified": Artisan.objects.filter(is_verified=True).count(),
            "not_verified": Artisan.objects.filter(is_verified=False).count(),
        },

        # =====================
        # KYC
        # =====================
        "kyc": {
            "pending": ArtisanKYC.objects.filter(statut='PENDING').count(),
            "approved": ArtisanKYC.objects.filter(statut='APPROVED').count(),
            "rejected": ArtisanKYC.objects.filter(statut='REJECTED').count(),
        },

        # =====================
        # MESSAGES
        # =====================
        "messages": {
            "conversations": Conversation.objects.count(),
            "total_messages": Message.objects.count(),
            "unread_messages": Message.objects.filter(is_read=False).count(),
        },

        # =====================
        # POSTS
        # =====================
        "posts": {
            "total": Post.objects.count(),
            "images": Post.objects.filter(media_type='IMAGE').count(),
            "videos": Post.objects.filter(media_type='VIDEO').count(),
            "total_likes": PostLike.objects.count(),
            "total_comments": PostComment.objects.count(),
        },

        # =====================
        # REPORTS
        # =====================
        "reports": {
            "total": Report.objects.count(),
            "pending": Report.objects.filter(status='PENDING').count(),
            "resolved": Report.objects.filter(status='RESOLVED').count(),
            "rejected": Report.objects.filter(status='REJECTED').count(),
        }
    }

    return JsonResponse(data)

from django.shortcuts import render

def admin_stats(request):
    # Affiche la page de statistiques
    return render(request, "admin_dashboard/stats.html")

# views.py
def admin_clients(request):
    clients = User.objects.filter(
        role='CLIENT',
        is_deleted=False
    ).values(
        'id',
        'nom',
        'prenom',
        'email',
        'telephone',
        'ville'
    )

    return JsonResponse({
        "clients": list(clients)
    })


@csrf_exempt
def post_like(request, post_id):
    """
    Bascule (toggle) l'état "Liké" pour un post par un utilisateur.
    Si le like existe, il est supprimé (unlike). S'il n'existe pas, il est créé (like).
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        
        if not user_id:
            return JsonResponse({'error': 'ID utilisateur requis'}, status=400)
            
        post = Post.objects.get(pk=post_id, is_deleted=False)
        user = User.objects.get(pk=user_id, is_deleted=False)
        
        # Vérifie si l'utilisateur a déjà liké ce post
        like_exists = PostLike.objects.filter(post=post, user=user).first()
        
        action = ""
        
        if like_exists:
            # UNLIKE: Supprimer le like existant
            like_exists.delete()
            post.likes_count -= 1
            action = "unliked"
        else:
            # LIKE: Créer un nouveau like
            PostLike.objects.create(
                post=post,
                user=user,
                type_like='LIKE' # En supposant que le type par défaut est LIKE
            )
            post.likes_count += 1
            action = "liked"
        
        post.save()
        
        return JsonResponse({
            'success': True,
            'message': f"Post {action} avec succès.",
            'action': action,
            'is_liked': action == 'liked',
            'likes_count': post.likes_count
        }, status=200)
            
    except Post.DoesNotExist:
        return JsonResponse({'error': 'Post non trouvé'}, status=404)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Utilisateur non trouvé'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)