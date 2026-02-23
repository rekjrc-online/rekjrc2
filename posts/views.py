from django.apps import apps
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.views import View
from django.views.generic import DetailView, CreateView
from rekjrc.base_models import Ownable
from .forms import PostForm
from .models import Post

def homepage(request):
    page = int(request.GET.get("page", 1))
    posts_per_page = 5
    start = (page - 1) * posts_per_page
    end = start + posts_per_page
    posts = Post.objects.all().order_by("-created_at")[start:end]
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        html = render_to_string("posts/list.html", {"posts": posts})
        end_reached = posts.count() < posts_per_page
        return JsonResponse({"html": html, "end": end_reached})
    return render(request, "homepage.html", {"posts": posts})

class PostDetail(DetailView):
    model = Post
    template_name = "posts/detail.html"
    context_object_name = "post"
    slug_field = "uuid"
    slug_url_kwarg = "post_uuid"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        post = self.object
        replies = post.replies.order_by('created_at')
        ctx['replies'] = replies
        ctx['parent_post'] = post.parent if hasattr(post, 'parent') else None
        return ctx

class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = "posts/form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        user_owned = {}
        for model in apps.get_models():
            if issubclass(model, Ownable) and model is not Ownable:
                qs = model.objects.filter(owner=self.request.user, is_active=True)
                if qs.exists():
                    user_owned[model.__name__.lower()] = qs
        kwargs['author_queryset'] = user_owned
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        owned_list = []
        for model in apps.get_models():
            if issubclass(model, Ownable) and model is not Ownable:
                qs = model.objects.filter(owner=self.request.user, is_active=True)
                for obj in qs:
                    owned_list.append(obj)
        ctx['user_owned'] = owned_list
        return ctx

class PostReplyView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = "posts/form.html"

    def dispatch(self, request, *args, **kwargs):
        self.parent_post = get_object_or_404(Post, uuid=kwargs["post_uuid"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        user_owned = {}
        for model in apps.get_models():
            if issubclass(model, Ownable) and model is not Ownable:
                qs = model.objects.filter(owner=self.request.user, is_active=True)
                if qs.exists():
                    user_owned[model.__name__.lower()] = qs
        kwargs['author_queryset'] = user_owned
        return kwargs

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.parent = self.parent_post
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['parent_post'] = getattr(self, 'parent_post', None)
        owned_list = []
        for model in apps.get_models():
            if issubclass(model, Ownable) and model is not Ownable:
                qs = model.objects.filter(owner=self.request.user, is_active=True)
                for obj in qs:
                    owned_list.append(obj)
        ctx['user_owned'] = owned_list
        return ctx

class PostRepliesAjax(View):
    def get(self, request, post_uuid, *args, **kwargs):
        post = get_object_or_404(Post, uuid=post_uuid)
        replies = post.replies.all()
        data = {
            "post_uuid": str(post.uuid),
            "replies": [
                {
                    "uuid": str(reply.uuid),
                    "content": reply.content,
                    "author": reply.author.username,
                }
                for reply in replies
            ]
        }
        return JsonResponse(data)

def toggle_like_ajax(request, post_uuid):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    post = get_object_or_404(Post, uuid=post_uuid)
    return JsonResponse({
        "success": True,
        "post_uuid": str(post.uuid),
    })


class ObjectPostsAjax(View):
    """
    Generic paginated posts endpoint for any model detail page.
    URL: /posts/for/<model_name>/<uuid>/?page=N
    Returns JSON {html, has_next} using the posts/list.html fragment.
    """
    POSTS_PER_PAGE = 5

    def get(self, request, model_name, uuid):
        from django.apps import apps
        from django.core.paginator import Paginator
        from django.contrib.contenttypes.models import ContentType as CT

        model = None
        for m in apps.get_models():
            if m._meta.verbose_name.lower().replace(" ", "") == model_name.lower().replace(" ", ""):
                model = m
                break
        if model is None:
            return JsonResponse({"html": "", "has_next": False}, status=404)

        obj = get_object_or_404(model, uuid=uuid)
        content_type = CT.objects.get_for_model(model)
        qs = Post.objects.filter(
            author_content_type=content_type,
            author_object_id=obj.id,
        ).order_by("-created_at")

        page_num = int(request.GET.get("page", 1))
        paginator = Paginator(qs, self.POSTS_PER_PAGE)
        page = paginator.get_page(page_num)

        html = render_to_string("posts/list.html", {"posts": page.object_list}, request=request)
        return JsonResponse({"html": html, "has_next": page.has_next()})