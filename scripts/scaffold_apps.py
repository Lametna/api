import os

APPS = [
    'authentication', 'users', 'friends', 'party', 'messages', 
    'notifications', 'games', 'communities', 'achievements', 
    'inventory', 'shop', 'leaderboards', 'analytics', 
    'creator', 'moderation', 'common'
]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPS_DIR = os.path.join(BASE_DIR, 'apps')

# Ensure core and config are packages
for d in ['core', 'config', 'config/settings', 'apps']:
    init_file = os.path.join(BASE_DIR, d, '__init__.py')
    os.makedirs(os.path.dirname(init_file), exist_ok=True)
    with open(init_file, 'w') as f:
        pass

for app in APPS:
    app_dir = os.path.join(APPS_DIR, app)
    os.makedirs(app_dir, exist_ok=True)
    
    files = {
        '__init__.py': '',
        'apps.py': f"from django.apps import AppConfig\n\nclass {app.capitalize()}Config(AppConfig):\n    default_auto_field = 'django.db.models.BigAutoField'\n    name = 'apps.{app}'\n",
        'models.py': "from django.db import models\nfrom core.models import BaseModel\n\n# Create your models here.\n",
        'urls.py': "from django.urls import path\n\napp_name = '{app}'\n\nurlpatterns = [\n    # path('', views.example_view, name='example'),\n]\n",
        'views.py': "from rest_framework.views import APIView\nfrom rest_framework.response import Response\n\n# Create your views here.\n",
        'serializers.py': "from rest_framework import serializers\n\n# Create your serializers here.\n",
        'services.py': "\"\"\"\nBusiness logic operations for the {app} domain.\n\"\"\"\n",
        'selectors.py': "\"\"\"\nDatabase query operations for the {app} domain.\n\"\"\"\n",
    }
    
    for filename, content in files.items():
        filepath = os.path.join(app_dir, filename)
        if not os.path.exists(filepath):
            with open(filepath, 'w') as f:
                f.write(content)

print("Scaffolded 16 Django apps successfully with Clean Architecture structure.")
