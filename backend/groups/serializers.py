from rest_framework import serializers
from .models import Group, GroupMember
from accounts.serializers import UserSerializer


class GroupMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = GroupMember
        fields = ['id', 'user', 'user_id', 'joined_at', 'left_at', 'is_active']
        read_only_fields = ['id']


class GroupSerializer(serializers.ModelSerializer):
    members = GroupMemberSerializer(source='memberships', many=True, read_only=True)
    created_by = UserSerializer(read_only=True)
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = [
            'id', 'name', 'description', 'default_currency',
            'created_by', 'members', 'member_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def get_member_count(self, obj):
        return obj.memberships.filter(is_active=True).count()


class GroupCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['name', 'description', 'default_currency']

    def create(self, validated_data):
        user = self.context['request'].user
        group = Group.objects.create(created_by=user, **validated_data)
        # Creator is automatically a member
        GroupMember.objects.create(
            group=group,
            user=user,
            joined_at=group.created_at.date(),
            is_active=True,
        )
        return group


class AddMemberSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    joined_at = serializers.DateField()

    def validate_user_id(self, value):
        from accounts.models import User
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError('User not found')
        return value


class UpdateMemberSerializer(serializers.Serializer):
    left_at = serializers.DateField(required=False, allow_null=True)
    is_active = serializers.BooleanField(required=False)
