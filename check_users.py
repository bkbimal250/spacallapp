import os
import django

# Setup django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.accounts.models.user import User

# Get one user and print all its fields and their values
user = User.objects.first()
if user:
    print(f"User: {user.email}")
    for field in user._meta.fields:
        print(f"Field: {field.name}, Value: {getattr(user, field.name)}")
else:
    print("No users found.")
