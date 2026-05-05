from django import forms
from django.db.models import Q
from .models import Race, RaceDriver, RaceJudgeDevice


def _user_devices(user):
    from devices.models import Device
    return Device.objects.filter(
        Q(owner_user=user) | Q(owner_team__members__user=user)
    ).distinct()


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
