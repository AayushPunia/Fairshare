from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Group, GroupMember
from .serializers import (
    GroupSerializer, GroupCreateSerializer,
    GroupMemberSerializer, AddMemberSerializer, UpdateMemberSerializer,
)
from accounts.models import User


class GroupListCreateView(generics.ListCreateAPIView):
    """
    GET: List all groups the current user is a member of.
    POST: Create a new group (creator auto-added as member).
    """
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return GroupCreateSerializer
        return GroupSerializer

    def get_queryset(self):
        return Group.objects.filter(
            memberships__user=self.request.user
        ).distinct().prefetch_related('memberships__user')


class GroupDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PUT/DELETE a specific group."""
    serializer_class = GroupSerializer

    def get_queryset(self):
        return Group.objects.filter(
            memberships__user=self.request.user
        ).distinct().prefetch_related('memberships__user')


class GroupMemberListView(APIView):
    """
    GET: List members of a group.
    POST: Add a member to a group.
    """
    def get(self, request, group_id):
        group = Group.objects.get(id=group_id)
        members = group.memberships.select_related('user').all()
        serializer = GroupMemberSerializer(members, many=True)
        return Response(serializer.data)

    def post(self, request, group_id):
        serializer = AddMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        group = Group.objects.get(id=group_id)
        user = User.objects.get(id=serializer.validated_data['user_id'])

        # Check if already a member
        existing = GroupMember.objects.filter(
            group=group, user=user, is_active=True
        ).first()
        if existing:
            return Response(
                {'error': f'{user.display_name} is already an active member'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        member = GroupMember.objects.create(
            group=group,
            user=user,
            joined_at=serializer.validated_data['joined_at'],
            is_active=True,
        )
        return Response(
            GroupMemberSerializer(member).data,
            status=status.HTTP_201_CREATED,
        )


class GroupMemberDetailView(APIView):
    """
    PATCH: Update a member (set left_at date, deactivate).
    DELETE: Remove a member from the group.
    """
    def patch(self, request, group_id, member_id):
        member = GroupMember.objects.get(id=member_id, group_id=group_id)
        serializer = UpdateMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if 'left_at' in serializer.validated_data:
            member.left_at = serializer.validated_data['left_at']
            member.is_active = False
        if 'is_active' in serializer.validated_data:
            member.is_active = serializer.validated_data['is_active']

        member.save()
        return Response(GroupMemberSerializer(member).data)

    def delete(self, request, group_id, member_id):
        member = GroupMember.objects.get(id=member_id, group_id=group_id)
        member.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
