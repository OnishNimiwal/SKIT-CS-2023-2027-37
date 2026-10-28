from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/chat/", include("chat.urls")),
    path("api/documents/", include("documents.urls")),
]

# Uploaded files are deliberately not served under /media/: they would be readable
# without signing in. Document content is only exposed through the owner-checked API.
