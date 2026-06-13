"""
URL configuration for FairShare.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/groups/', include('groups.urls')),
    path('api/expenses/', include('expenses.urls')),
    path('api/import/', include('importer.urls')),
]
