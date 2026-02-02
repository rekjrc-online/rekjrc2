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
        self.speaker = kwargs.pop("speaker", None)
        self.channel = kwargs.pop("channel", None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        if not self.user:
            raise forms.ValidationError("User is required.")
        if not self.speaker:
            raise forms.ValidationError("Speaker is required.")
        if not self.channel:
            raise forms.ValidationError("Channel is required.")
        if self.speaker != self.user:
            if not hasattr(self.speaker, "owner") or self.speaker.owner != self.user:
                raise forms.ValidationError("You may only speak as yourself or objects you own.")
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.user = self.user
        instance.speaker_content_type = ContentType.objects.get_for_model(self.speaker)
        instance.speaker_object_id = self.speaker.pk
        instance.channel_content_type = ContentType.objects.get_for_model(self.channel)
        instance.channel_object_id = self.channel.pk
        if commit:
            instance.save()
            instance.refresh_from_db()
        return instance
