"""
URL configuration for FairShare.

In production, Django serves the React SPA's index.html for any non-API route.
This enables client-side routing (React Router) to work with direct URL access.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/groups/', include('groups.urls')),
    path('api/expenses/', include('expenses.urls')),
    path('api/import/', include('importer.urls')),
]

# In production, serve React's index.html for all non-API routes
# This allows React Router to handle client-side routing
if not settings.DEBUG:
    urlpatterns += [
        re_path(r'^(?!api/|admin/|static/).*$',
                TemplateView.as_view(template_name='index.html'),
                name='spa-fallback'),
    ]
