

INSTALLED_APPS = [
    # ...
    "rest_framework",
    "django_filters",
    "cms",
]

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
        # we can swap TokenAuthentication for simplejwt if we want later
    ],
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Root urls.py:
# from django.conf import settings
# from django.conf.urls.static import static
# urlpatterns = [
#     ...
#     path("api/cms/", include("cms.urls")),
# ]
# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# pip install:
# djangorestframework django-filter
