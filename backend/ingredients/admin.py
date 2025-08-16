from django.contrib import admin
from .models import Ingredient


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)  # фильтр по единице измерения
    ordering = ('name',)  # сортировка по названию
    readonly_fields = ('id',)  # поле id только для чтения

    fieldsets = (
        (None, {
            'fields': ('name', 'measurement_unit'),
            'description': 'Управление ингредиентами'
        }),
    )