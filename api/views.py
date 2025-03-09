from django.shortcuts import redirect
from django.contrib.auth.models import User
from rest_framework import generics
from .serializers import UserSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from allauth.socialaccount.models import SocialToken, SocialAccount
from django.contrib.auth.decorators import login_required
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.contrib.gis.geos import GEOSGeometry
from .models import PolygonFeature  # Use your correct model name
from .serializers import PolygonFeatureSerializer  # Make sure you have a serializer



User = get_user_model()

class UserCreate(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

class UserDetailView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
    


@login_required
def google_login_callback(request):
    user = request.user

    social_accounts = SocialAccount.objects.filter(user=user)
    print("Social Account for user:", social_accounts)

    social_account = social_accounts.first()

    if not social_account:
        print("No social account for user:", user)
        return redirect('http://localhost:5173/login/callback/?error=NoSocialAccount')

    token = SocialToken.objects.filter(account=social_account, account__providers='google').first()

    if token:
        print('Google token found:', token.token)
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        return redirect(f'http://localhost:5173/login/callback/?access_token={access_token}')
    else:
        print('No Google token found for user:', user)
        return redirect(f'http://localhost:5173/login/callback/?error=NoGoogleToken')


@csrf_exempt
def validate_google_token(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            google_access_token = data.get('access_token')
            print(google_access_token)

            if not google_access_token:
                return JsonResponse({'detail': 'Access Token is missing.'}, status=400)
            
            return JsonResponse({'valid': True})
        except json.JSONDecodeError:
            return JsonResponse({'detail': 'Invalid JSON.'}, status=400)

    return JsonResponse({'detail': 'Method not allowed.'}, status=405)






@api_view(['GET', 'POST'])
def polygon_list(request):
    """Handles GET (list all) and POST (create) requests."""
    if request.method == 'GET':
        polygons = PolygonFeature.objects.all()
        serializer = PolygonFeatureSerializer(polygons, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        data = request.data
        print(data)
        try:
            # Convert WKT string to GEOS Geometry
            data['geom'] = GEOSGeometry(data.get('geom'))
            serializer = PolygonFeatureSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
def polygon_detail(request, pk):
    """Handles GET (retrieve), PUT (update), and DELETE (remove) requests."""
    try:
        polygon = PolygonFeature.objects.get(pk=pk)
    except PolygonFeature.DoesNotExist:
        return Response({'error': 'Polygon not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = PolygonFeatureSerializer(polygon)
        return Response(serializer.data)

    elif request.method == 'PUT':
        data = request.data
        try:
            data['geom'] = GEOSGeometry(data.get('geom'))
            serializer = PolygonFeatureSerializer(polygon, data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        polygon.delete()
        return Response({'message': 'Polygon deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
