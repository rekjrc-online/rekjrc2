from django.urls import reverse
from django.db import models
from rekjrc.base_models import BaseModel, Ownable
from locations.models import Location
from teams.models import Team
from django.urls import reverse
from locations.models import Location
from teams.models import Team

class Club(BaseModel, Ownable):
    advanced_relations = (
        ("locations", "Location"),
        ("members", "Member"),
        ("teams", "Team") )

    def __str__(self):
        return self.display_name

    def get_absolute_url(self):
        return reverse("clubs:detail", kwargs={"uuid": self.uuid})

    @property
    def has_advanced(self):
        return True

class ClubLocation(BaseModel):
    club = models.ForeignKey(
        Club,
        on_delete=models.CASCADE,
        related_name="locations")
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name="clubs")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["club", "location"],
                name="unique_club_location")]

    def __str__(self):
        return f"{self.club.display_name} @ {self.location}"

class ClubMember(BaseModel):
    club = models.ForeignKey(
        Club,
        on_delete=models.CASCADE,
        related_name="members")
    user = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="club_memberships")
    invited_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        related_name="club_invitations",
        null=True, blank=True)
    role = models.CharField(max_length=100, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["club", "user"],
                name="unique_club_member")]

    def __str__(self):
        role_display = f" ({self.role})" if self.role else ""
        return f"{self.user} @ {self.club}{role_display}"

class ClubTeam(BaseModel):
    club = models.ForeignKey(
        Club,
        on_delete=models.CASCADE,
        related_name="teams")
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="teams")

    def __str__(self):
        return f"{self.club.display_name} @ {self.team}"

