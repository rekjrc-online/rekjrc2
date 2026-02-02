from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import ForeignKey

class CrudAuthMixin(LoginRequiredMixin):
    login_url = "/accounts/login/"
    redirect_field_name = "next"

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
        "race_finished",
        "allow_followers",
        "enable_chat" ]

    bottom_fields = [
        'is_active',
        'allow_followers',
        'enable_chat' ]

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
                    related_fields = [
                        (f.verbose_name, getattr(value, f.name))
                        for f in value._meta.fields
                        if f.name not in ("id", "uuid")
                    ]
                    field_values.append((field.verbose_name, related_fields))
                else:
                    field_values.append((field.verbose_name, value))
            for field_name in self.bottom_fields:
                for i, (verbose, val) in enumerate(field_values):
                    if verbose.lower().replace(" ", "_") == field_name:
                        field_values.append(field_values.pop(i))
                        break
            ctx["field_values"] = field_values
        return ctx

    def form_valid(self, form):
        instance = form.instance
        model = instance.__class__
        if any(f.name == "owner" for f in model._meta.fields):
            instance.owner = self.request.user
        return super().form_valid(form)