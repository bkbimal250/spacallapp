from rest_framework import serializers
from .models import Contact


class ContactSerializer(serializers.ModelSerializer):
    total_calls = serializers.IntegerField(read_only=True)

    class Meta:
        model = Contact
        fields = [
            'id', 'name', 'phone_number', 'email', 'country', 'city',
            'created_by', 'updated_by', 'created_at', 'total_calls'
        ]

    def validate_phone_number(self, value):
        instance = self.instance

        if Contact.objects.filter(phone_number=value).exclude(id=instance.id if instance else None).exists():
            raise serializers.ValidationError("Phone number already exists")

        return value

    def validate_email(self, value):
        instance = self.instance

        if value and Contact.objects.filter(email=value).exclude(id=instance.id if instance else None).exists():
            raise serializers.ValidationError("Email already exists")

        return value