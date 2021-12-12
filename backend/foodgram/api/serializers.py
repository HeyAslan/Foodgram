from djoser.serializers import UserCreateSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from recipes.models import Ingredient, IngredientRecipe, Recipe, Tag
from users.models import User


class UserRegistrationSerializer(UserCreateSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name',
                  'last_name', 'password')
        read_only_fields = ('id',)


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name',
                  'last_name', 'is_subscribed')
        read_only_fields = ('id', 'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request.user.is_authenticated:
            return False
        return obj.subscribed_users.filter(user=request.user).exists()


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        read_only_fields = ('name', 'measurement_unit',)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug', 'color')
        read_only_fields = ('name', 'slug', 'color')


class IngredientRecipeSerializer(serializers.ModelSerializer):

    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all()
    )
    name = serializers.StringRelatedField(
        source='ingredient.name'
    )
    measurement_unit = serializers.StringRelatedField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientRecipe
        fields = ['id', 'amount', 'name', 'measurement_unit']

    def validate_amount(self, value):
        if (value < 1):
            raise serializers.ValidationError(
                'Нельзя указывать отрицательное количество ингредиентов.')
        return value


class RecipeCreateSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    ingredients = IngredientRecipeSerializer(
        many=True,
        source='ingredients_amount'
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'name', 'text', 'cooking_time', 'image')
        read_only_fields = ('id', 'author')

    def validate_cooking_time(self, value):
        if (value < 1):
            raise serializers.ValidationError(
                'Нельзя указывать отрицательное время приготовления.')
        return value

    def validate(self, data):

        request = self.context['request']
        if (request.method == 'POST' and Recipe.objects.filter(
                name=data['name'], text=data['text']).exists()):
            raise ValidationError('Такой рецепт уже существует')

        validated_tags = set()
        for tag in data['tags']:
            if tag.id in validated_tags:
                raise serializers.ValidationError(
                    'Тег можно указать только 1 раз')
            else:
                validated_tags.add(tag.id)

        validated_ingredients = set()
        for ingredient_amount in data['ingredients_amount']:
            if ingredient_amount['ingredient'].id in validated_ingredients:
                raise serializers.ValidationError(
                    'Ингредиент можно указать только 1 раз')
            else:
                validated_ingredients.add(ingredient_amount['ingredient'].id)

        return data

    @staticmethod
    def add_ingredients(recipe, ingredients_data):
        for ingredient_data in ingredients_data:
            IngredientRecipe.objects.create(
                recipe=recipe,
                amount=ingredient_data.get('amount'),
                ingredient=ingredient_data.get('ingredient')
            )

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients_amount')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.add(*tags)
        self.add_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        if 'tags' in validated_data:
            tags = validated_data.pop('tags')
            instance.tags.clear()
            instance.tags.add(*tags)
        if 'ingredients_amount' in validated_data:
            ingredients_data = validated_data.pop('ingredients_amount')
            IngredientRecipe.objects.filter(recipe=instance).delete()
            self.add_ingredients(instance, ingredients_data)
        return super().update(instance, validated_data)


class RecipeGetSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True)
    image = Base64ImageField()
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'text', 'cooking_time', 'image')

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if not request.user.is_authenticated:
            return False
        return obj.is_favorited.filter(id=request.user.id).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if not request.user.is_authenticated:
            return False
        return obj.is_in_shopping_cart.filter(id=request.user.id).exists()

    def get_ingredients(self, obj):
        return IngredientRecipeSerializer(
            obj.ingredients_amount, many=True).data


class RecipeReducedSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'cooking_time', 'image')


class SubscriptionSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count')

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    # Сериализатор используется только для авторов,
    # на которых подписан текущий пользователь
    def get_is_subscribed(self, obj):
        return True

    def get_recipes(self, obj):
        request = self.context.get('request')
        if request is not None:
            recipes_limit = request.query_params.get('recipes_limit')
            if recipes_limit is not None:
                recipes = obj.recipes.all()[:int(recipes_limit)]
        else:
            recipes = obj.recipes.all()
        serializer = RecipeReducedSerializer(recipes, many=True)
        return serializer.data
