from django.apps import apps
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.db.models import Exists, OuterRef
from django.http import JsonResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views import View
from django.views.generic import DetailView, CreateView
from rekjrc.base_models import Ownable
from .forms import PostForm
from .models import Post, PostLike

class VerifiedRequiredMixin(LoginRequiredMixin):
    """
    Requires login (via LoginRequiredMixin) AND Account.is_verified --
    posting/replying is restricted to verified accounts. An unverified
    logged-in user is bounced to their account page with an explanatory
    message instead of the login-page redirect LoginRequiredMixin would
    otherwise give a logged-out visitor.
    """
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.is_verified:
            messages.error(
                request,
                "Your account is not verified. You must verify your account before you can post/reply.")
            return redirect("accounts:account")
        return super().dispatch(request, *args, **kwargs)

def _annotate_liked(queryset, user):
    """Annotate a Post queryset with liked_by_user for the given user."""
    if user and user.is_authenticated:
        return queryset.annotate(
            liked_by_user=Exists(
                PostLike.objects.filter(post=OuterRef("pk"), user=user)
            )
        )
    return queryset

def homepage(request):
    try:
        page = int(request.GET.get("page", 1))
    except (TypeError, ValueError):
        page = 1
    if page < 1:
        page = 1
    posts_per_page = 5
    start = (page - 1) * posts_per_page
    end = start + posts_per_page
    posts = _annotate_liked(
        Post.objects.all().order_by("-created_at"), request.user
    )[start:end]
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        html = render_to_string("posts/list.html", {"posts": posts}, request=request)
        end_reached = len(posts) < posts_per_page
        return JsonResponse({"html": html, "end": end_reached})
    return render(request, "homepage.html", {"posts": posts})

class PostDetail(DetailView):
    model = Post
    template_name = "posts/detail.html"
    context_object_name = "post"
    slug_field = "uuid"
    slug_url_kwarg = "post_uuid"

    def get_context_data(self, **kwargs):
        from django.core.paginator import Paginator

        ctx = super().get_context_data(**kwargs)
        post = self.object
        replies_qs = _annotate_liked(
            post.replies.order_by('created_at'), self.request.user
        )
        paginator = Paginator(replies_qs, PostRepliesAjax.REPLIES_PER_PAGE)
        ctx['replies'] = paginator.get_page(1)
        ctx['parent_post'] = post.parent if hasattr(post, 'parent') else None
        return ctx

class PostCreateView(VerifiedRequiredMixin, CreateView):
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

class PostReplyView(VerifiedRequiredMixin, CreateView):
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
    """
    Paginated replies endpoint for a post's detail page.
    URL: /posts/replies/ajax/<post_uuid>/?page=N
    Returns JSON {html, has_next} using the posts/list.html fragment --
    same contract as ObjectPostsAjax, since both feed scroll_replies.js.
    """
    REPLIES_PER_PAGE = 5

    def get(self, request, post_uuid, *args, **kwargs):
        from django.core.paginator import Paginator

        post = get_object_or_404(Post, uuid=post_uuid)
        replies = _annotate_liked(
            post.replies.order_by("created_at"), request.user
        )

        try:
            page_num = int(request.GET.get("page", 1))
        except (TypeError, ValueError):
            page_num = 1
        if page_num < 1:
            page_num = 1
        paginator = Paginator(replies, self.REPLIES_PER_PAGE)
        page = paginator.get_page(page_num)

        html = render_to_string("posts/list.html", {"posts": page.object_list}, request=request)
        return JsonResponse({"html": html, "has_next": page.has_next()})

@login_required
def toggle_like_ajax(request, post_uuid):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    post = get_object_or_404(Post, uuid=post_uuid)
    like, created = PostLike.objects.get_or_create(user=request.user, post=post)
    if not created:
        # Already liked — remove it
        like.delete()
        liked = False
    else:
        liked = True
    return JsonResponse({
        "success": True,
        "post_uuid": str(post.uuid),
        "liked": liked,
        "likes_count": post.likes_count,
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
        qs = _annotate_liked(
            Post.objects.filter(
                author_content_type=content_type,
                author_object_id=obj.id,
            ).order_by("-created_at"),
            request.user,
        )

        try:
            page_num = int(request.GET.get("page", 1))
        except (TypeError, ValueError):
            page_num = 1
        if page_num < 1:
            page_num = 1
        paginator = Paginator(qs, self.POSTS_PER_PAGE)
        page = paginator.get_page(page_num)

        html = render_to_string("posts/list.html", {"posts": page.object_list}, request=request)
        return JsonResponse({"html": html, "has_next": page.has_next()})