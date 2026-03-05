from rest_framework import serializers
from .models import Contact


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = '__all__'
        read_only_fields = ('id', 'created_at')
        extra_kwargs = {
            'name': {'required': True},
            'phone_number': {'required': True},
            'email': {'required': False},
            'country': {'required': False},
            'city': {'required': False},
        }

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