from django.db import models

class Ingredient(models.Model):
    name = models.CharField(max_length=256, unique=True)
    measurement_unit = models.CharField(max_length=256)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'



class Tag(models.Model):
    name = models.CharField(max_length=256, unique=True)
    slug = models.SlugField(unique=True)
    # TODO: colour = 

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Recipe(models.Model):
    name = models.CharField(max_length=256)
    text = models.TextField()
    cooking_time = models.PositiveSmallIntegerField()
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientRecipe',
    )

    # TODO: 
    # author =     
    # image = 
    # tags = models.ManyToManyField(Tag, through='TagRecipe')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class IngredientRecipe(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
    )
    amount = models.PositiveSmallIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['ingredient', 'recipe'], name='unique_ingredient_recipe'
            ),
        ]
    
