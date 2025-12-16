# marketplaceapp/models.py
from django.db import models

# --------------------------
# 1️⃣ Users
# --------------------------
class User(models.Model):
    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('ARTISAN', 'Artisan'),
        ('CLIENT', 'Client'),
    )

    nom = models.CharField(max_length=150)
    prenom = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    ville = models.CharField(max_length=100, blank=True, null=True)
    password = models.CharField(max_length=128)  # stocke le hash
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='CLIENT')
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nom} {self.prenom} ({self.role})"

# --------------------------
# 2️⃣ Activites
# --------------------------
class Activite(models.Model):
    nom = models.CharField(max_length=100)
    description = models.TextField(blank=True)

# --------------------------
# 3️⃣ Specialites
# --------------------------
class Specialite(models.Model):
    activite = models.ForeignKey(Activite, on_delete=models.CASCADE)
    nom = models.CharField(max_length=100)
    description = models.TextField(blank=True)

# --------------------------
# 4️⃣ Artisans
# --------------------------
class Artisan(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    adresse = models.CharField(max_length=255, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='artisan_created_by')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='artisan_updated_by')

# --------------------------
# 5️⃣ ArtisanSpecialites
# --------------------------
class ArtisanSpecialite(models.Model):
    artisan = models.ForeignKey(Artisan, on_delete=models.CASCADE)
    specialite = models.ForeignKey(Specialite, on_delete=models.CASCADE)

# --------------------------
# 6️⃣ ArtisanKYC
# --------------------------
class ArtisanKYC(models.Model):
    STATUT_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected')
    )
    artisan = models.ForeignKey(Artisan, on_delete=models.CASCADE)
    photo_profil = models.ImageField(upload_to='kyc/photos/')
    cni = models.ImageField(upload_to='kyc/cni/')  # maintenant c'est bien une image
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='PENDING')
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='kyc_verified_by')
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

# --------------------------
# 7️⃣ Feedbacks
# --------------------------
class Feedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    note = models.IntegerField()
    commentaire = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

# --------------------------
# 8️⃣ Conversations
# --------------------------
class Conversation(models.Model):
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conv_user1')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conv_user2')
    last_message = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

# --------------------------
# 9️⃣ Messages
# --------------------------
class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    contenu = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

# --------------------------
# 🔟 Posts
# --------------------------
class Post(models.Model):
    MEDIA_TYPE_CHOICES = (
        ('IMAGE', 'Image'),
        ('VIDEO', 'Video')
    )
    artisan = models.ForeignKey(Artisan, on_delete=models.CASCADE)
    titre = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    media_url = models.FileField(upload_to='posts/')
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES)
    media_size = models.FloatField(null=True, blank=True)
    media_duration = models.DurationField(null=True, blank=True)
    media_thumbnail = models.ImageField(upload_to='posts/thumbnails/', blank=True, null=True)
    media_mime = models.CharField(max_length=50, blank=True)
    likes_count = models.IntegerField(default=0)
    comments_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

# --------------------------
# 1️⃣1️⃣ PostLikes
# --------------------------
class PostLike(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type_like = models.CharField(max_length=10, default='LIKE')
    created_at = models.DateTimeField(auto_now_add=True)

# --------------------------
# 1️⃣2️⃣ PostComments
# --------------------------
class PostComment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    commentaire = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

# --------------------------
# 1️⃣3️⃣ Notifications
# --------------------------
class Notification(models.Model):
    NOTIF_TYPE_CHOICES = (
        ('KYC', 'KYC'),
        ('MESSAGE', 'Message'),
        ('POST', 'Post'),
        ('SYSTEM', 'System')
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=NOTIF_TYPE_CHOICES)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

# --------------------------
# 1️⃣4️⃣ Subscriptions
# --------------------------
class Subscription(models.Model):
    subscriber = models.ForeignKey(User, on_delete=models.CASCADE)
    artisan = models.ForeignKey(Artisan, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

# --------------------------
# 1️⃣5️⃣ Reporting
# --------------------------
class Report(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('RESOLVED', 'Resolved'),
        ('REJECTED', 'Rejected')
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    artisan = models.ForeignKey(Artisan, on_delete=models.CASCADE, null=True, blank=True)
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

# --------------------------
# 1️⃣6️⃣ AuditLogs
# --------------------------
class AuditLog(models.Model):
    table_name = models.CharField(max_length=50)
    record_id = models.IntegerField()
    action = models.CharField(max_length=20)  # CREATE, UPDATE, DELETE, APPROVE
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
