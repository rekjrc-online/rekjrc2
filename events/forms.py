from django import forms
from django.forms import ModelForm
from django.apps import apps

from .models import Event


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
        self._save_related(instance)
        return instance

    def _save_related(self, event):
        for key, cfg in self.RELATED_CONFIG.items():
            through = apps.get_model(cfg["through"])
            field_name = cfg["field"]
            selected = self.cleaned_data.get(key, [])

            # Clear existing
            through.objects.filter(event=event).delete()

            # Recreate
            through.objects.bulk_create(
                [
                    through(
                        event=event,
                        **{field_name: obj},
                    )
                    for obj in selected
                ]
            )
