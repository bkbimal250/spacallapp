import os
import django
import sys

# Setup django environment
project_path = os.getcwd()
if project_path not in sys.path:
    sys.path.append(project_path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.accounts.models.user import User

# Get one user and print all its attributes
try:
    user = User.objects.first()
    if user:
        print(f"User: {user.email}")
        # Print all dictionary attributes
        for key, value in user.__dict__.items():
            if 'password' in key.lower():
                print(f"Attr: {key}, Value: {value}")
    else:
        print("No users found.")
except Exception as e:
    print(f"Error: {e}")
