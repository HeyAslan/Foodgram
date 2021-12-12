from django.contrib import admin

from .models import Ingredient, IngredientRecipe, Recipe, Subscription, Tag


class RecipeIngredientInline(admin.TabularInline):
    model = Recipe.ingredients.through
    extra = 1


class RecipeAdmin(admin.ModelAdmin):
    inlines = (RecipeIngredientInline,)
    list_display = ('name', 'author')
    list_filter = ('name', 'author', 'tags')
    fields = ('name', 'text', 'cooking_time', 'tags',
              'image', 'author', 'favorites_count')
    readonly_fields = ('favorites_count',)

    def favorites_count(self, obj):
        return obj.is_favorited.count()
    favorites_count.short_description = 'Число добавлений в избранное'


class TagAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'author')
    list_filter = ('user', 'author')


admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(IngredientRecipe)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
