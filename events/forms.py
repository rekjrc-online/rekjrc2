from django import forms
from django.contrib.auth import get_user_model
from django.forms import ModelForm
from django.apps import apps

from .models import Event

User = get_user_model()

class EventForm(ModelForm):
    RELATED_CONFIG = {
        "teams": {
            "model": "teams.Team",
            "through": "events.EventTeam",
            "field": "team",
            "related_name": "event_teams",
            "label": "Teams",
        },
        "locations": {
            "model": "locations.Location",
            "through": "events.EventLocation",
            "field": "location",
            "related_name": "event_locations",
            "label": "Locations",
        },
        "clubs": {
            "model": "clubs.Club",
            "through": "events.EventClub",
            "field": "club",
            "related_name": "event_clubs",
            "label": "Clubs",
        },
        "stores": {
            "model": "stores.Store",
            "through": "events.EventStore",
            "field": "store",
            "related_name": "event_stores",
            "label": "Stores",
        },
        "races": {
            "model": "races.Race",
            "through": "events.EventRace",
            "field": "race",
            "related_name": "event_races",
            "label": "Races",
        },
    }

    class Meta:
        model = Event
        fields = [
            "display_name",
            "event_date",
            "event_time",
            "event_days",
            "is_active",
        ]
        widgets = {
            "display_name": forms.TextInput(attrs={"placeholder": "Enter event name"}),
            "event_date": forms.DateInput(attrs={"type": "date"}),
            "event_time": forms.TimeInput(attrs={"type": "time"}),
            "event_days": forms.NumberInput(attrs={"min": 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        instance = kwargs.get("instance")

        for key, cfg in self.RELATED_CONFIG.items():
            model = apps.get_model(cfg["model"])
            through = apps.get_model(cfg["through"])

            self.fields[key] = forms.ModelMultipleChoiceField(
                queryset=model.objects.all(),
                required=False,
                widget=forms.CheckboxSelectMultiple,
                label=cfg["label"],
            )

            # Pre-populate when editing
            if instance and instance.pk:
                self.fields[key].initial = (
                    model.objects.filter(
                        **{
                            f"{cfg['related_name']}__event": instance
                        }
                    )
                )

    def save(self, commit=True):
        instance = super().save(commit)
        if instance.pk:
            self._save_related(instance)
        return instance

    def _save_related(self, event):
        for key, cfg in self.RELATED_CONFIG.items():
            through = apps.get_model(cfg["through"])
            field_name = cfg["field"]
            selected = self.cleaned_data.get(key, [])
            through.objects.filter(event=event).delete()
            through.objects.bulk_create(
                [
                    through(
                        event=event,
                        **{field_name: obj},
                    )
                    for obj in selected
                ]
            )


class EventCheckinForm(forms.Form):
    """
    Used by events.views.Checkin_ (the staff walk-up check-in page): staff
    search for the participant's account (rendered as a clickable list —
    see events/checkin.html), then scan/type the RFID lanyard code to link
    it to that account for this event.
    """
    rfid_code = forms.CharField(
        max_length=64,
        label="RFID code",
        widget=forms.TextInput(attrs={
            "placeholder": "Scan or type the lanyard code",
            "autofocus": True,
            "autocomplete": "off",
        }))
    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        widget=forms.HiddenInput)

    def __init__(self, *args, event=None, **kwargs):
        self.event = event
        super().__init__(*args, **kwargs)

    def clean_rfid_code(self):
        return self.cleaned_data["rfid_code"].strip().upper()
