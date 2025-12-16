from django.contrib import admin
from django.urls import path, include
# IMPORTS NÉCESSAIRES
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('marketplaceapp.urls')),
]
# **********************************************
# LIGNE CRUCIALE pour servir les fichiers MEDIA en mode DEBUG
# **********************************************
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)