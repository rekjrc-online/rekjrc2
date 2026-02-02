from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView, RetrieveAPIView
from posts.models import Post
from .serializers import PostSerializer

class PostListAPIView(ListAPIView):
    queryset = Post.objects.all().order_by("-created_at")
    serializer_class = PostSerializer

class PostDetailAPIView(RetrieveAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    lookup_field = "uuid"

class RelatedPostsAPIView(ListAPIView):
    serializer_class = PostSerializer
    model_class = None
    def get_queryset(self):
        if not self.model_class:
            raise ValueError("model_class must be set for RelatedPostsAPIView")
        obj = get_object_or_404(self.model_class, uuid=self.kwargs["uuid"])
        content_type = ContentType.objects.get_for_model(self.model_class)
        return Post.objects.filter(
            author_content_type=content_type,
            author_object_id=obj.id
        ).order_by("-created_at")
