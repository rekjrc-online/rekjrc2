from rest_framework import serializers
from posts.models import Post

class PostSerializer(serializers.ModelSerializer):
    author_info = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            "uuid",
            "created_at",
            "author_info",
            "content",
            "display_content" ]

    def get_author_info(self, obj):
        author = obj.author
        if author is None:
            return None
        data = {
            "type": author.__class__.__name__ }
        if hasattr(author, "uuid"):
            data["uuid"] = str(author.uuid)
        if hasattr(author, "display_name"):
            data["display_name"] = author.display_name

        return data