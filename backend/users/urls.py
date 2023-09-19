from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CustomUserViewSet
from foodgram.settings import APP_PREFIX_2

app_name = APP_PREFIX_2

router_v1 = DefaultRouter()

router_v1.register('users', CustomUserViewSet, basename='users')

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router_v1.urls)),
    path('', include('djoser.urls')),
]
