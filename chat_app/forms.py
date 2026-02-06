from django import forms
from django.contrib.contenttypes.models import ContentType
from .models import ChatMessage

class ChatMessageForm(forms.ModelForm):
    class Meta:
        model = ChatMessage
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Type your message…",
                }
            )
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        self.channel = kwargs.pop("channel", None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()

        if self.user:
            self.instance.user = self.user

        if self.channel:
            self.instance.channel_content_type = ContentType.objects.get_for_model(self.channel)
            self.instance.channel_object_id = self.channel.pk

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.user = self.user
        instance.channel_content_type = ContentType.objects.get_for_model(self.channel)
        instance.channel_object_id = self.channel.pk
        if commit:
            instance.save()
            instance.refresh_from_db()
        return instance
