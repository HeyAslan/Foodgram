import os

from django.conf import settings
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import status
from rest_framework.response import Response


def related_field_add_remove(obj, related_field, request, serializer,
                             error_message_get, error_message_delete):
    queryset = getattr(obj, related_field, None)
    if queryset is None:
        return Response(status=status.HTTP_400_BAD_REQUEST)
    if request.method == 'GET':
        if queryset.filter(id=request.user.id).exists():
            return Response(error_message_get,
                            status=status.HTTP_400_BAD_REQUEST)
        queryset.add(request.user)
        serializer = serializer(obj)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    if request.method == 'DELETE':
        if not queryset.filter(id=request.user.id).exists():
            return Response(error_message_delete,
                            status=status.HTTP_400_BAD_REQUEST)
        queryset.remove(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


def create_pdf(buffer, shopping_cart):

    def set_style(pdf, text):
        pdf.setFont('Verdana', 20)
        pdf.drawCentredString(300, 770, 'СПИСОК ПОКУПОК')
        pdf.line(30, 750, 550, 750)
        text.setFont('Verdana', 12)
        text.setLeading(18)

    def make_content(pdf, shopping_cart):
        pages = [shopping_cart[x:x + 30] for x in range(
            0, len(shopping_cart), 30)]

        font = os.path.join(settings.BASE_DIR, 'fonts/Verdana.ttf')
        pdfmetrics.registerFont(TTFont('Verdana', font))
        item_index = 1

        for page in pages:
            text = pdf.beginText(40, 680)
            set_style(pdf, text)

            for item in page:
                text.textLine(
                    f'{item_index}. {item["ingredient__name"].capitalize()} — '
                    f'{item["amount"]} {item["ingredient__measurement_unit"]}'
                )
                item_index += 1
            pdf.drawText(text)
            pdf.showPage()

    pdf = canvas.Canvas(buffer)
    make_content(pdf, shopping_cart)
    pdf.save()
