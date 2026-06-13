from django.urls import path
from . import views

urlpatterns = [
    path('', views.GroupListCreateView.as_view(), name='group-list-create'),
    path('<int:pk>/', views.GroupDetailView.as_view(), name='group-detail'),
    path('<int:group_id>/members/', views.GroupMemberListView.as_view(), name='group-members'),
    path('<int:group_id>/members/<int:member_id>/', views.GroupMemberDetailView.as_view(), name='group-member-detail'),
]
