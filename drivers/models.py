from rekjrc.base_models import BaseModel, Ownable
from django.urls import reverse

class Driver(BaseModel, Ownable):
    def __str__(self):
        return self.display_name or f"Driver {self.pk}"

    def get_absolute_url(self):
        return reverse("drivers:detail", kwargs={"uuid": self.uuid})