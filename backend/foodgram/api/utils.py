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
