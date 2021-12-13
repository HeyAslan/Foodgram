import io
import os

from django.conf import settings
from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from djoser.views import UserViewSet as BaseUserViewSet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from recipes.models import (Ingredient, IngredientRecipe,
                            Recipe, Subscription, Tag)
from users.models import User
from .filters import RecipeFilterSet
from .mixins import ListRetrieveViewSet
from .pagination import CustomPagination
from .permissions import IsAuthorOrStaffOrReadOnly
from .serializers import (IngredientSerializer, RecipeCreateSerializer,
                          RecipeGetSerializer, RecipeReducedSerializer,
                          SubscriptionSerializer, TagSerializer)
from .utils import related_field_add_remove


class UserViewSet(BaseUserViewSet):
    http_method_names = ['get', 'post', 'delete']
    pagination_class = CustomPagination

    def destroy(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=False, methods=['GET'])
    def me(self, request, *args, **kwargs):
        return super().me(request, *args, **kwargs)

    @action(detail=True,
            methods=['GET', 'DELETE'],
            permission_classes=(IsAuthenticated,))
    def subscribe(self, request, **kwargs):
        """
        Подписаться/отписаться от пользователя
        """
        author = self.get_object()
        if request.method == 'GET':
            if author.subscribed_users.filter(user=request.user).exists():
                return Response(
                    f'Вы уже подписаны на пользователя {author.username}',
                    status=status.HTTP_400_BAD_REQUEST
                )
            Subscription.objects.create(user=request.user, author=author)
            serializer = SubscriptionSerializer(author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if not author.subscribed_users.filter(user=request.user).exists():
                return Response(
                    f'Вы не подписаны на пользователя {author.username}',
                    status=status.HTTP_400_BAD_REQUEST
                )
            get_object_or_404(Subscription, user=request.user,
                              author=author).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False,
            methods=['GET'],
            permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        """
        Подписки пользователя
        """
        authors = User.objects.filter(subscribed_users__user=request.user)
        page = self.paginate_queryset(authors)
        if page is not None:
            serializer = SubscriptionSerializer(
                page, context={'request': self.request}, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = SubscriptionSerializer(
            authors, context={'request': self.request}, many=True)
        return self.get_paginated_response(serializer.data)


class IngredientViewSet(ListRetrieveViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    permission_classes = (AllowAny,)
    filter_backends = (SearchFilter,)
    search_fields = ('^name',)


class TagViewSet(ListRetrieveViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = (AllowAny,)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = CustomPagination
    permission_classes = (IsAuthorOrStaffOrReadOnly,)
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = RecipeFilterSet

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return RecipeGetSerializer
        return RecipeCreateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True,
            methods=['GET', 'DELETE'],
            permission_classes=(IsAuthenticated,))
    def favorite(self, request, **kwargs):
        """
        Добавить/удалить рецепт из избранного
        """
        recipe = self.get_object()
        error_message_get = (f'Рецепт "{recipe.name}"'
                             ' уже добавлен в ваше избранное')
        error_message_delete = (f'Рецепт "{recipe.name}"'
                                'отсутствует в вашем избранном')
        return related_field_add_remove(
            obj=recipe,
            related_field='is_favorited',
            request=request,
            serializer=RecipeReducedSerializer,
            error_message_get=error_message_get,
            error_message_delete=error_message_delete
        )

    @action(detail=True,
            methods=['GET', 'DELETE'],
            permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, **kwargs):
        """
        Добавить/удалить рецепт из списка покупок
        """
        recipe = self.get_object()
        error_message_get = (f'Рецепт "{recipe.name}"'
                             ' уже добавлен в ваши покупки')
        error_message_delete = (f'Рецепт "{recipe.name}"'
                                'отсутствует в ваших покупках')
        return related_field_add_remove(
            obj=recipe,
            related_field='is_in_shopping_cart',
            request=request,
            serializer=RecipeReducedSerializer,
            error_message_get=error_message_get,
            error_message_delete=error_message_delete
        )

    @action(detail=False,
            methods=['GET'],
            permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request):
        """
        Скачать список покупок
        """
        shopping_cart = IngredientRecipe.objects.filter(
            recipe__is_in_shopping_cart__id=request.user.id).values(
                'ingredient__name', 'ingredient__measurement_unit').annotate(
                    amount=Sum('amount'))

        def make_content(pdf):
            font = os.path.join(settings.BASE_DIR, 'fonts/Verdana.ttf')
            pdfmetrics.registerFont(TTFont('Verdana', font))
            pdf.setFont('Verdana', 20)
            pdf.drawCentredString(300, 770, 'СПИСОК ПОКУПОК')
            pdf.line(30, 750, 550, 750)
            text = pdf.beginText(40, 680)
            text.setFont('Verdana', 12)
            text.setLeading(18)
            i = 1
            for item in shopping_cart:
                text.textLine(
                    f'{i}. {item["ingredient__name"].capitalize()} — '
                    f'{item["amount"]} {item["ingredient__measurement_unit"]}'
                )
                i += 1
            pdf.drawText(text)

        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer)
        make_content(pdf)
        pdf.showPage()
        pdf.save()
        buffer.seek(0)

        return FileResponse(buffer, as_attachment=True,
                            filename='shopping_cart.pdf')
