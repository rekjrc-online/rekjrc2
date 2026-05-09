from django import forms
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

from .models import Device


def get_owner_choices(user):
    """
    Build the (value, label) choices for entities `user` is allowed to assign a
    device to. Values are encoded as 'kind-id' (e.g. 'club-12'); the special
    value 'user' means the user themselves.
    """
    from teams.models import Team
    from clubs.models import Club
    from locations.models import Location

    user_label = (user.get_full_name() or user.email or str(user)).strip()
    choices = [('user', f'Myself ({user_label})')]

    teams = (Team.objects
             .filter(Q(owner=user) | Q(members__user=user))
             .distinct()
             .order_by('display_name'))
    choices += [(f'team-{t.id}', f'Team: {t.display_name}') for t in teams]

    clubs = (Club.objects
             .filter(Q(owner=user) | Q(members__user=user))
             .distinct()
             .order_by('display_name'))
    choices += [(f'club-{c.id}', f'Club: {c.display_name}') for c in clubs]

    locations = Location.objects.filter(owner=user).order_by('display_name')
    choices += [(f'location-{l.id}', f'Location: {l.display_name}') for l in locations]

    return choices


def resolve_owner_choice(user, raw):
    """
    Reverse of `get_owner_choices`: turn a raw value like 'club-12' or 'user'
    into a (ContentType, object_id) pair, validating that `user` is allowed
    to assign a device to that entity. Raises forms.ValidationError on failure.
    """
    from teams.models import Team
    from clubs.models import Club
    from locations.models import Location

    if raw == 'user':
        return ContentType.objects.get_for_model(user.__class__), user.id

    try:
        kind, pk = raw.split('-', 1)
        pk = int(pk)
    except (ValueError, AttributeError):
        raise forms.ValidationError("Invalid owner selection.")

    if kind == 'team':
        qs = Team.objects.filter(Q(owner=user) | Q(members__user=user)).distinct()
        model = Team
    elif kind == 'club':
        qs = Club.objects.filter(Q(owner=user) | Q(members__user=user)).distinct()
        model = Club
    elif kind == 'location':
        qs = Location.objects.filter(owner=user)
        model = Location
    else:
        raise forms.ValidationError("Invalid owner selection.")

    if not qs.filter(pk=pk).exists():
        raise forms.ValidationError(
            "You don't have permission to assign a device to that entity."
        )

    return ContentType.objects.get_for_model(model), pk


class DeviceForm(forms.ModelForm):
    """
    Manual create/edit of a Device's basic fields. Ownership is set elsewhere:
      - on Create_, the view auto-assigns the creating user as owner+claimer
      - on Scan_, the user picks an owner via DeviceClaimForm
    """
    class Meta:
        model = Device
        fields = ['mac', 'name', 'description']
        widgets = {
            'mac': forms.TextInput(attrs={'placeholder': 'AA:BB:CC:DD:EE:FF'}),
            'name': forms.TextInput(attrs={'placeholder': 'Enter device name'}),
            'description': forms.Textarea(attrs={
                'rows': 3, 'placeholder': 'Optional description'
            }),
        }

    def __init__(self, *args, user=None, **kwargs):
        # `user` accepted for compatibility with view get_form_kwargs; not
        # currently used here since ownership is handled by the view.
        super().__init__(*args, **kwargs)


class DeviceClaimForm(forms.Form):
    """
    Used by the Scan view to claim an unlinked Device on behalf of `user` and
    assign it to one of their allowable owner entities.
    """
    device = forms.ModelChoiceField(
        queryset=Device.objects.none(),
        widget=forms.HiddenInput,
    )
    owner = forms.ChoiceField(choices=[], label="Assign to")

    def __init__(self, *args, user=None, **kwargs):
        if user is None:
            raise ValueError("DeviceClaimForm requires a `user` keyword argument")
        self.user = user
        super().__init__(*args, **kwargs)
        self.fields['device'].queryset = Device.objects.filter(
            content_type__isnull=True
        )
        self.fields['owner'].choices = get_owner_choices(user)

    def clean(self):
        cleaned = super().clean()
        raw = cleaned.get('owner')
        if raw:
            ct, oid = resolve_owner_choice(self.user, raw)
            cleaned['owner_content_type'] = ct
            cleaned['owner_object_id']    = oid
        return cleaned
