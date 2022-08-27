from django.shortcuts import redirect


def unauthenticated_user(view_func):
    """Отправляет пользователя на главную страницу,
    если он уже авторизовался"""
    def wrapper_func(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("index_page")
    
        return view_func(request, *args, **kwargs)
  
    return wrapper_func


def for_allowed_users_only(allowed_roles):
    """Блокирует доступ пользователям без заданной роли,
    при этом возвращая на главную страницу"""
    def decorator(view_func):
        def wrapper_func(request, *args, **kwargs):
            if request.user.username in allowed_roles:
                return view_func(request, *args, **kwargs)
            
            return redirect("index_page")
        return wrapper_func
    return decorator
