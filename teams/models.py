from django.db import models
from django.conf import settings
from django.urls import reverse
from rekjrc.base_models import BaseModel, Ownable

class Team(BaseModel, Ownable):
    @property
    def has_advanced(self):
        return True

    def __str__(self):
        return self.display_name

    def get_absolute_url(self):
            return reverse("teams:detail", kwargs={"uuid": self.uuid})

class TeamMember(BaseModel):
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='members'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='team_memberships'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["team", "user"],
                name="unique_team_member"
            )
        ]

    def __str__(self):
        return f"{self.user} @ {self.team}"
