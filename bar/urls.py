from django.urls import path
from . import views

app_name = "bar"

urlpatterns = [
    path("", views.public_menu, name="public_menu"),
    path("m/", views.public_qr_menu, name="public_qr_menu"),  # 👈 ESTA ES LA CLAVE
    path("menu/<slug:slug>/", views.collection_menu, name="collection_menu"),
    path("cocktail/<int:cocktail_id>/", views.cocktail_detail, name="cocktail_detail"),
    path("unlock-suggestions/", views.unlock_suggestions, name="unlock_suggestions"),
    path("my-bar/", views.my_bar_dashboard, name="my_bar_dashboard"),
    path("diagnose-db-2026/", views.diagnose_db, name="diagnose_db"),
]
