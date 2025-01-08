from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from .models import Chat, Message
from .serializers import UserSerializer, ChatSerializer, MessageSerializer, CreateChatSerializer
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import ensure_csrf_cookie


@ensure_csrf_cookie
def index(request):
   return render(request, 'index.html')

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class ChatViewSet(viewsets.ModelViewSet):
    serializer_class = ChatSerializer

    def get_queryset(self):
        return Chat.objects.filter(participants=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = CreateChatSerializer(data=request.data)
        if serializer.is_valid():
            chat = serializer.save()
            chat.participants.add(request.user)
            return Response(ChatSerializer(chat).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        chat = get_object_or_404(Chat, pk=pk)
        messages = Message.objects.filter(chat=chat).order_by('timestamp')
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)



class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer

    def create(self, request, *args, **kwargs):
        chat_id = request.data.get('chat')
        chat = get_object_or_404(Chat, id=chat_id)
        if request.user not in chat.participants.all():
            return Response({"error": "User is not a part of this chat"}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(sender=request.user, chat=chat)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
