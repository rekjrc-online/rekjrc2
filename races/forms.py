from django import forms
from .models import Race, RaceDriver, RaceJudgeDevice


def _user_devices(user):
    # Reuses devices.views._user_devices (the canonical "devices this user
    # can pick from" query: claimed_by, or GFK-owned by the user/a team/club/
    # location they belong to) instead of keeping a second copy here. This
    # local copy used to filter on Device.owner_user / Device.owner_team --
    # separate FK fields that were dropped from the Device model back in
    # migrations 0004/0005 when ownership moved to a single GenericForeignKey
    # (content_type/object_id). Nothing updated this copy when that happened,
    # so it kept raising FieldError ("Cannot resolve keyword 'owner_user'")
    # every time RaceForm/RaceJudgeDeviceForm tried to scope the device
    # dropdown for a user.
    from devices.views import _user_devices as _devices_user_devices
    return _devices_user_devices(user)


class RaceForm(forms.ModelForm):
    class Meta:
        model = Race
        fields = [
            'display_name', 'race_type', 'event', 'location', 'track',
            'club', 'team', 'store', 'transponder', 'device', 'entry_locked',
            'race_finished', 'is_active'
        ]
        widgets = {
            'entry_locked': forms.CheckboxInput(),
            'race_finished': forms.CheckboxInput(),
            'is_active': forms.CheckboxInput(),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields['device'].queryset = _user_devices(user)
            self.fields['device'].required = False


class RaceDriverForm(forms.ModelForm):
    class Meta:
        model = RaceDriver
        fields = ['race', 'user', 'build', 'driver', 'transponder']


class RaceJudgeDeviceForm(forms.ModelForm):
    class Meta:
        model = RaceJudgeDevice
        fields = ['judge', 'device']

    def __init__(self, *args, race=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if race and race.judge_team:
            judge_user_ids = race.judge_team.members.values_list('user_id', flat=True)
            from django.contrib.auth import get_user_model
            User = get_user_model()
            self.fields['judge'].queryset = User.objects.filter(pk__in=judge_user_ids)
        if user is not None:
            self.fields['device'].queryset = _user_devices(user)
            self.fields['device'].required = False
