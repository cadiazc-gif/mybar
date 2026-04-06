from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from .models import Cocktail, Tag, MenuCollection, Ingredient, ShoppingItem


def public_menu(request):
    cocktails = Cocktail.objects.filter(
        visible_public=True
    ).prefetch_related("tags", "recipe_items__ingredient")

    show_all = request.GET.get("all") == "1"
    status_filter = request.GET.get("status")
    tag_filter = request.GET.get("tag")
    collection_slug = request.GET.get("collection")

    if collection_slug:
        collection = MenuCollection.objects.filter(
            slug=collection_slug,
            is_public=True
        ).first()
        if collection:
            cocktails = collection.cocktails.filter(
                visible_public=True
            ).prefetch_related("tags", "recipe_items__ingredient")
    else:
        collection = None

    cocktail_data = []

    for cocktail in cocktails:
        availability = cocktail.check_availability()
        cocktail_data.append({
            "object": cocktail,
            "status": availability["status"],
            "missing": availability["missing"],
            "substituted": availability["substituted"],
        })

    if not show_all:
        cocktail_data = [
            c for c in cocktail_data
            if c["status"] in ["available", "available_with_substitute"]
        ]

    if status_filter:
        cocktail_data = [c for c in cocktail_data if c["status"] == status_filter]

    if tag_filter:
        cocktail_data = [
            c for c in cocktail_data
            if c["object"].tags.filter(name__iexact=tag_filter).exists()
        ]

    all_tags = Tag.objects.all().order_by("name")

    context = {
        "cocktail_data": cocktail_data,
        "status_filter": status_filter,
        "tag_filter": tag_filter,
        "all_tags": all_tags,
        "show_all": show_all,
        "collection": collection,
    }
    return render(request, "bar/public_menu.html", context)


def cocktail_detail(request, cocktail_id):
    cocktail = get_object_or_404(
        Cocktail.objects.prefetch_related("tags", "recipe_items__ingredient"),
        id=cocktail_id,
        visible_public=True,
    )

    availability = cocktail.check_availability()

    context = {
        "cocktail": cocktail,
        "availability": availability,
    }
    return render(request, "bar/cocktail_detail.html", context)


def unlock_suggestions(request):
    ingredients = Ingredient.objects.all()
    cocktails = Cocktail.objects.filter(
        visible_public=True
    ).prefetch_related("recipe_items__ingredient")

    suggestion_map = {}

    for ingredient in ingredients:
        if ingredient.in_stock:
            continue

        unlock_count = 0

        for cocktail in cocktails:
            availability = cocktail.check_availability()
            missing = availability["missing"]

            if len(missing) == 1 and ingredient.name in missing:
                unlock_count += 1

        if unlock_count > 0:
            suggestion_map[ingredient.name] = unlock_count

    suggestions = sorted(suggestion_map.items(), key=lambda x: x[1], reverse=True)

    return render(request, "bar/unlock_suggestions.html", {
        "suggestions": suggestions
    })


def my_bar_dashboard(request):
    ingredients_in_stock = Ingredient.objects.filter(in_stock=True).order_by("category", "name")
    ingredients_low = Ingredient.objects.filter(is_low=True).order_by("name")
    shopping_items = ShoppingItem.objects.filter(
        pending=True,
        purchased=False
    ).select_related("ingredient")

    cocktails = Cocktail.objects.filter(
        visible_public=True
    ).prefetch_related("recipe_items__ingredient")

    available = []
    almost_available = []
    unavailable = []

    for cocktail in cocktails:
        availability = cocktail.check_availability()

        if availability["status"] in ["available", "available_with_substitute"]:
            available.append(cocktail)
        elif availability["status"] == "almost_available":
            almost_available.append({
                "cocktail": cocktail,
                "missing": availability["missing"],
            })
        else:
            unavailable.append(cocktail)

    context = {
        "ingredients_in_stock": ingredients_in_stock,
        "ingredients_low": ingredients_low,
        "shopping_items": shopping_items,
        "available_count": len(available),
        "almost_available": almost_available,
        "unavailable_count": len(unavailable),
    }

    return render(request, "bar/my_bar_dashboard.html", context)


def public_qr_menu(request):
    collection = MenuCollection.objects.filter(
        is_active=True,
        is_public=True
    ).first()

    if not collection:
        return render(request, "bar/public_menu.html", {
            "cocktail_data": [],
            "collection": None,
            "all_tags": [],
            "show_all": False,
        })

    cocktails = collection.cocktails.filter(
        visible_public=True
    ).prefetch_related("tags", "recipe_items__ingredient")

    cocktail_data = []

    for cocktail in cocktails:
        availability = cocktail.check_availability()

        if availability["status"] in ["available", "available_with_substitute"]:
            cocktail_data.append({
                "object": cocktail,
                "status": availability["status"],
                "missing": availability["missing"],
                "substituted": availability["substituted"],
            })

    all_tags = Tag.objects.all().order_by("name")

    return render(request, "bar/public_menu.html", {
        "cocktail_data": cocktail_data,
        "collection": collection,
        "all_tags": all_tags,
        "show_all": False,
    })


def collection_menu(request, slug):
    collection = get_object_or_404(
        MenuCollection,
        slug=slug,
        is_public=True
    )

    cocktails = collection.cocktails.filter(
        visible_public=True
    ).prefetch_related("tags", "recipe_items__ingredient")

    cocktail_data = []

    for cocktail in cocktails:
        availability = cocktail.check_availability()

        if availability["status"] in ["available", "available_with_substitute"]:
            cocktail_data.append({
                "object": cocktail,
                "status": availability["status"],
                "missing": availability["missing"],
                "substituted": availability["substituted"],
            })

    all_tags = Tag.objects.all().order_by("name")

    context = {
        "cocktail_data": cocktail_data,
        "all_tags": all_tags,
        "collection": collection,
        "show_all": False,
    }
    return render(request, "bar/public_menu.html", context)


def runtime_diagnose(request):
    from django.contrib.auth import get_user_model
    from django.db import connection
    from django.conf import settings
    from django.http import HttpResponse
    import os

    User = get_user_model()

    lines = []
    lines.append(f"ENGINE: {settings.DATABASES['default']['ENGINE']}")
    lines.append(f"NAME: {settings.DATABASES['default']['NAME']}")
    lines.append(f"HOST: {settings.DATABASES['default'].get('HOST')}")
    lines.append(f"PORT: {settings.DATABASES['default'].get('PORT')}")
    lines.append(f"DATABASE_URL present: {'DATABASE_URL' in os.environ}")
    lines.append(f"Connected vendor: {connection.vendor}")

    try:
        usernames = list(User.objects.values_list("username", flat=True))
        lines.append(f"user count: {len(usernames)}")
        lines.append(f"usernames: {', '.join(usernames) if usernames else '(none)'}")
    except Exception as e:
        lines.append(f"user query ERROR: {e}")

    return HttpResponse("<br>".join(lines))