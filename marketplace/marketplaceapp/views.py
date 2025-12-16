import json
from django.http import JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password, check_password
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.db.models import Q

# Importez vos modèles User, Artisan, ArtisanKYC, etc. ici
from .models import User, Artisan, ArtisanKYC, Activite, Specialite 
from .forms import ArtisanCreationForm, ArtisanKYCForm

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
        artisans = list(Artisan.objects.filter(is_deleted=False).values())
        return JsonResponse({'artisans': artisans}, status=200)
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