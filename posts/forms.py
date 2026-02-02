from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django import forms

from .models import Post

from builds.models import Build
from clubs.models import Club
from drivers.models import Driver
from events.models import Event
from locations.models import Location
from races.models import Race
from stores.models import Store
from teams.models import Team
from tracks.models import Track

AUTHOR_TYPE_MAP = {
    "build": Build,
    "club": Club,
    "driver": Driver,
    "event": Event,
    "location": Location,
    "race": Race,
    "store": Store,
    "team": Team,
    "track": Track }

class PostForm(forms.ModelForm):
    author_choice = forms.ChoiceField(label="Post as")

    class Meta:
        model = Post
        fields = ['content', 'image']
        widgets = {'content':forms.Textarea(attrs={'rows':4,'placeholder':"What's on your mind?"})}

    def __init__(self, *args, author_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        choices = []
        if author_queryset:
            for key in author_queryset:
                qs = author_queryset[key].filter(is_active=True)
                for obj in qs:
                    label = key.title() + " - " + str(obj)
                    value = key + ":" + str(obj.uuid)
                    choices.append((value, label))
        self.fields["author_choice"].choices = choices
        new_fields = {}
        new_fields["author_choice"] = self.fields["author_choice"]
        for field_name in self.fields:
            if field_name != "author_choice":
                new_fields[field_name] = self.fields[field_name]
        self.fields = new_fields

    def save(self, commit=True):
        instance = super().save(commit=False)
        raw = self.cleaned_data["author_choice"]
        type_key, obj_uuid = raw.split(":", 1)
        model = AUTHOR_TYPE_MAP.get(type_key)
        if not model:
            raise ValueError("Invalid author type")
        author = model.objects.get(uuid=obj_uuid)
        if not getattr(author, "is_active", False):
            raise ValidationError("Selected author is not active")
        instance.author_content_type = ContentType.objects.get_for_model(author)
        instance.author_object_id = author.pk
        if commit:
            instance.save()
        return instance