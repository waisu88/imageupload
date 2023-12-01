from django.contrib.auth import authenticate, login, logout
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.reverse import reverse
from django.contrib.auth.models import User
from .serializers import LoginSerializer


class AuthAPIOverview(APIView):

    def get(self, request):
        routes = {
            "Login": request.build_absolute_uri(reverse(('login'))),
            "Logout": request.build_absolute_uri(reverse(('logout'))),
        }
        return Response(routes)


class LoginAPIView(APIView):
    queryset = User.objects.all()
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():      
            data = serializer.data
            username = data['username']
            password = data['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                if request.user != user:
                    logout(request)
                redirect_message = f"You can now redirect to images service: {request.build_absolute_uri(reverse(('images-api-overview')))}"
                if request.user.is_authenticated:
                    return Response({
                        "message": "You are already logged in.",
                        "redirect_message": redirect_message
                                     })
                login(request, user)
                return Response({
                    "message": "You have been successfully logged in.",
                    "redirect_message": redirect_message
                                 })
            return Response({"message": "error", "details": ["Invalid credentials"]})
        

class LogoutAPIView(APIView):
    def get(self, request):
        logout(request)
        return Response({"message": "Successfully logouted."})