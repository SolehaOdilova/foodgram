from django.db.models import Sum

from .models import Ingredient, RecipeIngredientAmount


def build_shopping_list(user):
    shopping_data = (
        RecipeIngredientAmount.objects.filter(
            recipe__in=user.shopping_cart_recipes.values_list("id", flat=True)
        )
        .values("ingredient")
        .annotate(total=Sum("amount"))
    )

    ingredient_map = Ingredient.objects.in_bulk(
        [item["ingredient"] for item in shopping_data]
    )

    lines = ["Список покупок:\n"]

    for item in shopping_data:
        ingr = ingredient_map.get(item["ingredient"])
        if ingr:
            unit = ingr.measurement_unit.strip() or "шт."
            lines.append(f"{ingr.name} ({unit}) — {item['total']}")

    return "\n".join(lines)
