import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

users = User.objects.all()
for u in users:
    print(f"User email: {u.email}")
    u.set_password('vigopadamu')
    u.save()
print('Password updated for all users')
