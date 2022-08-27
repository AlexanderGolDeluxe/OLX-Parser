from django.apps import AppConfig


class OlxparserConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "olxparser"
    verbose_name = "Парсер объявлений с OLX"

    def ready(self):
        """Создаёт тестовых пользователей при первом запуске сервера"""
        from django.contrib.auth.models import User

        user_model_objs = User.objects
        default_users_data = {
            "user1": {
                "first_name": "Пользователь №1",
                "password": "user123"
            },
            "user2": {
                "first_name": "Пользователь №2",
                "password": "user456"
            },
            "user3": {
                "first_name": "Пользователь №3",
                "password": "user789"
            }
        }
        existing_usernames = {
            user_obj.username for user_obj in user_model_objs.filter(
                username__in=default_users_data.keys()
            )
        }
        for username, user_auth_data in default_users_data.items():
            if not username in existing_usernames:
                user_model_objs.create_user(
                    username=username,
                    first_name=user_auth_data.get("first_name"),
                    password=user_auth_data.get("password"))
