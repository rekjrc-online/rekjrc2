from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import redirect_to_login
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import ForeignKey

DETAIL_POSTS_PER_PAGE = 5

class CrudAuthMixin(LoginRequiredMixin):
    login_url = "/accounts/login/"
    redirect_field_name = "next"

class PublicDetailMixin:
    """
    Use in place of CrudAuthMixin on a DetailView (alongside CrudContextMixin)
    for "detail" pages that should be visible beyond just the object's owner.

    Historically Detail_ views used CrudAuthMixin + CrudContextMixin, and
    CrudContextMixin.get_queryset() restricts any model with an `owner`
    field to the requesting user's own objects -- correct for Edit/Delete,
    but it meant a detail page 404'd for any logged-in user who wasn't the
    owner. This mixin fixes that: any logged-in user can view any object's
    detail page.

    Anonymous (logged-out) visitors additionally need the object's
    `is_public` flag set True (see rekjrc.base_models.Ownable.is_public,
    default False) -- otherwise they're redirected to log in, same as
    CrudAuthMixin/LoginRequiredMixin would do. Models without an
    `is_public` field (e.g. Device, which isn't Ownable) stay
    login-required for everyone.

    Owner-only actions on the same detail page (Edit/Delete/Advanced/
    Check-in/etc.) are untouched by this -- those views still use
    CrudAuthMixin + CrudContextMixin's owner-scoped get_queryset, and stay
    hidden in templates behind the `is_owner` flag that
    CrudContextMixin.get_context_data() computes per-object regardless of
    which mixin the Detail_ view itself uses.
    """
    login_url = "/accounts/login/"
    redirect_field_name = "next"

    def get_queryset(self):
        return self.model._default_manager.all()

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not request.user.is_authenticated and not getattr(self.object, "is_public", False):
            return redirect_to_login(
                request.get_full_path(), self.login_url, self.redirect_field_name)
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

class CrudContextMixin:
    model_name = None
    model_name_plural = None
    action = None

    auto_exclude = [
        "id",
        "uuid",
        "owner",
        "created_at",
        "updated_at",
        "entry_locked",
        "race_finished", ]

    bottom_fields = [
        'is_active',
        'is_public',
        'allow_followers',
        'enable_chat', ]

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for name in self.auto_exclude:
            form.fields.pop(name, None)
        for field in self.bottom_fields:
            if field in form.fields:
                field_obj = form.fields.pop(field)
                form.fields[field] = field_obj
        return form

    def get_context_data(self, **kwargs):
        from posts.models import Post
        from posts.views import ObjectPostsAjax
        ctx = super().get_context_data(**kwargs)
        model = self.model
        ctx["model_name"] = self.model_name or model._meta.verbose_name
        ctx["model_name_plural"] = self.model_name_plural or model._meta.verbose_name_plural
        ctx["action"] = self.action
        obj = ctx.get("object")
        if obj:
            ctx["is_owner"] = hasattr(obj, "owner") and obj.owner == self.request.user
            field_values = []
            for field in model._meta.fields:
                if field.name in self.auto_exclude:
                    continue
                value = getattr(obj, field.name)
                if isinstance(field, ForeignKey) and value:
                    field_values.append((field.verbose_name, str(value)))
                else:
                    field_values.append((field.verbose_name, value))
            for field_name in self.bottom_fields:
                for i, (verbose, val) in enumerate(field_values):
                    if verbose.lower().replace(" ", "_") == field_name:
                        field_values.append(field_values.pop(i))
                        break
            ctx["field_values"] = field_values

            # First page of posts for this object (AJAX loads subsequent pages)
            content_type = ContentType.objects.get_for_model(model)
            posts_qs = Post.objects.filter(
                author_content_type=content_type,
                author_object_id=obj.id,
            ).order_by("created_at")
            paginator = Paginator(posts_qs, DETAIL_POSTS_PER_PAGE)
            first_page = paginator.get_page(1)
            ctx["object_posts"] = first_page
            ctx["object_posts_model_name"] = model._meta.verbose_name.lower().replace(" ", "")

        return ctx

    def form_valid(self, form):
        instance = form.instance
        model = instance.__class__
        if any(f.name == "owner" for f in model._meta.fields):
            instance.owner = self.request.user
        return super().form_valid(form)
    
    def get_queryset(self):
        qs = super().get_queryset()
        model = self.model
        if any(f.name == "owner" for f in model._meta.fields):
            qs = qs.filter(owner=self.request.user)
        return qs