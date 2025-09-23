from django.apps import AppConfig

class FormsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "src.forms"   # importante para usar import 'src.forms...'
    label = "forms"      # app label usado em makemigrations/migrate
