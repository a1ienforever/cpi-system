from rest_framework import serializers
from apps.users.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'full_name', 'role', 'is_active')
        read_only_fields = ('id',)

    def validate_role(self, value):
        if value not in ['employee', 'manager', 'admin']:
            raise serializers.ValidationError("Invalid role")
        return value
