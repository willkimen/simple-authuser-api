from rest_framework.response import Response
from user_app.serializers import UserRegistrationSerializer
from rest_framework.decorators import api_view
from rest_framework import status


@api_view(['POST'])
def register(request):
    serializer = UserRegistrationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({'validation_errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    user = serializer.save()
    return Response({'user_id': user.id, 'message': 'User registered successfully'}, status=status.HTTP_201_CREATED)
