from django.db import models


class IngredientCategory(models.TextChoices):
    SPIRIT = "spirit", "Destilado"
    LIQUEUR = "liqueur", "Licor"
    BITTER = "bitter", "Bitter"
    MIXER = "mixer", "Mixer"
    JUICE = "juice", "Jugo"
    FRUIT = "fruit", "Fruta / Verdura"
    SYRUP = "syrup", "Jarabe"
    GARNISH = "garnish", "Guarnición"
    ICE = "ice", "Hielo"
    OTHER = "other", "Otro"


class Ingredient(models.Model):
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(
        max_length=20,
        choices=IngredientCategory.choices,
        default=IngredientCategory.OTHER,
    )
    in_stock = models.BooleanField(default=False, verbose_name="Disponible en mi bar")
    is_low = models.BooleanField(default=False, verbose_name="Se está acabando")
    add_to_shopping = models.BooleanField(default=False, verbose_name="Agregar a compra")
    notes = models.TextField(blank=True)

    substitutes = models.ManyToManyField(
        "self",
        symmetrical=False,
        blank=True,
        related_name="can_replace_for",
        verbose_name="Reemplazos posibles",
    )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if (not self.in_stock) and self.add_to_shopping:
            ShoppingItem.objects.get_or_create(
                ingredient=self,
                pending=True,
                purchased=False,
            )


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Cocktail(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255, blank=True)
    image = models.URLField(blank=True, verbose_name="URL de imagen")
    preparation = models.TextField(verbose_name="Preparación paso a paso")
    personal_rating = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Nota personal (0-5)"
    )
    favorite = models.BooleanField(default=False, verbose_name="Favorito")
    visible_public = models.BooleanField(default=True, verbose_name="Visible en menú público")
    tags = models.ManyToManyField(Tag, blank=True)

    def __str__(self):
        return self.name

    def get_required_items(self):
        return self.recipe_items.filter(required=True).select_related("ingredient")

    def get_optional_items(self):
        return self.recipe_items.filter(optional=True).select_related("ingredient")

    def check_availability(self):
        required_items = self.get_required_items()

        if not required_items.exists():
            return {
                "status": "no_recipe",
                "missing": [],
                "substituted": [],
            }

        missing = []
        substituted = []

        for item in required_items:
            ingredient = item.ingredient

            if ingredient.in_stock:
                continue

            substitute_found = False

            if item.allow_substitute:
                for sub in ingredient.substitutes.all():
                    if sub.in_stock:
                        substitute_found = True
                        substituted.append({
                            "original": ingredient.name,
                            "substitute": sub.name,
                        })
                        break

            if not substitute_found:
                missing.append(ingredient.name)

        if len(missing) == 0 and len(substituted) == 0:
            status = "available"
        elif len(missing) == 0 and len(substituted) > 0:
            status = "available_with_substitute"
        elif len(missing) == 1:
            status = "almost_available"
        else:
            status = "unavailable"

        return {
            "status": status,
            "missing": missing,
            "substituted": substituted,
        }

    def availability_status(self):
        return self.check_availability()["status"]

    def missing_ingredients(self):
        return self.check_availability()["missing"]

    def substitute_summary(self):
        return self.check_availability()["substituted"]


class CocktailIngredient(models.Model):
    UNIT_CHOICES = [
        ("oz", "oz"),
        ("ml", "ml"),
        ("dash", "dash"),
        ("drop", "gota"),
        ("piece", "unidad"),
        ("slice", "rodaja"),
        ("leaf", "hoja"),
        ("top", "top / completar"),
        ("other", "otro"),
    ]

    cocktail = models.ForeignKey(Cocktail, on_delete=models.CASCADE, related_name="recipe_items")
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name="used_in")
    quantity = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default="oz")
    order = models.PositiveIntegerField(default=1)
    required = models.BooleanField(default=True, verbose_name="Obligatorio")
    optional = models.BooleanField(default=False, verbose_name="Opcional")
    allow_substitute = models.BooleanField(default=True, verbose_name="Permite reemplazo")
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["order"]
        unique_together = ("cocktail", "ingredient", "order")

    def __str__(self):
        return f"{self.cocktail.name} - {self.ingredient.name}"


class ShoppingItem(models.Model):
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    pending = models.BooleanField(default=True)
    added_at = models.DateTimeField(auto_now_add=True)
    purchased = models.BooleanField(default=False)

    def __str__(self):
        return f"Comprar: {self.ingredient.name}"


class MenuCollection(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255, blank=True)
    slug = models.SlugField(unique=True, help_text="Ej: menu-viernes")
    is_public = models.BooleanField(default=True, verbose_name="Visible públicamente")

    is_active = models.BooleanField(
        default=False,
        verbose_name="Colección activa para QR"
    )

    cocktails = models.ManyToManyField(Cocktail, blank=True, related_name="collections")

    def __str__(self):
        return self.name