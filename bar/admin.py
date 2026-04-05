from django.contrib import admin
from .models import Ingredient, Tag, Cocktail, CocktailIngredient, ShoppingItem, MenuCollection

class CocktailIngredientInline(admin.TabularInline):
    model = CocktailIngredient
    extra = 1


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "in_stock", "is_low", "add_to_shopping")
    list_filter = ("category", "in_stock", "is_low", "add_to_shopping")
    search_fields = ("name",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(Cocktail)
class CocktailAdmin(admin.ModelAdmin):
    list_display = ("name", "favorite", "personal_rating", "visible_public", "availability_badge")
    list_filter = ("favorite", "visible_public", "tags")
    search_fields = ("name", "description")
    inlines = [CocktailIngredientInline]

    def availability_badge(self, obj):
        status = obj.availability_status()

        labels = {
            "available": "Disponible",
            "available_with_substitute": "Disponible con reemplazo",
            "almost_available": "Casi disponible",
            "unavailable": "No disponible",
            "no_recipe": "Sin receta",
        }
        return labels.get(status, status)

    availability_badge.short_description = "Disponibilidad"


@admin.register(ShoppingItem)
class ShoppingItemAdmin(admin.ModelAdmin):
    list_display = ("ingredient", "pending", "purchased", "added_at")
    list_filter = ("pending", "purchased")

@admin.register(MenuCollection)
class MenuCollectionAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_public", "is_active")
    list_filter = ("is_public", "is_active")
    search_fields = ("name", "description")
    filter_horizontal = ("cocktails",)

    def save_model(self, request, obj, form, change):
        if obj.is_active:
            MenuCollection.objects.update(is_active=False)
        super().save_model(request, obj, form, change)
