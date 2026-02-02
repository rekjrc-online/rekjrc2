from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    path("", views.List_.as_view(), name="list"),
    path("create/", views.Create_.as_view(), name="create"),
    path("<uuid:uuid>/", views.Detail_.as_view(), name="detail"),
    path("<uuid:uuid>/edit/", views.Update_.as_view(), name="edit"),
    path("<uuid:uuid>/delete/", views.Delete_.as_view(), name="delete"),
    path("<uuid:uuid>/advanced/", views.Advanced_.as_view(), name="advanced"),
    path("<uuid:uuid>/clubs/add/", views.EventClubAdd.as_view(), name="club-add"),
    path("<uuid:uuid>/locations/add/", views.EventLocationAdd.as_view(), name="location-add"),
    path("<uuid:uuid>/races/add/", views.EventRaceAdd.as_view(), name="race-add"),
    path("<uuid:uuid>/stores/add/", views.EventStoreAdd.as_view(), name="store-add"),
    path("<uuid:uuid>/teams/add/", views.EventTeamAdd.as_view(), name="team-add"),
    path("<uuid:uuid>/clubs/<int:event_club_id>/remove/", views.EventClubRemove.as_view(), name="club-remove"),
    path("<uuid:uuid>/locations/<int:event_location_id>/remove/", views.EventLocationRemove.as_view(), name="location-remove"),
    path("<uuid:uuid>/races/<int:event_race_id>/remove/", views.EventRaceRemove.as_view(), name="race-remove"),
    path("<uuid:uuid>/stores/<int:event_store_id>/remove/", views.EventStoreRemove.as_view(), name="store-remove"),
    path("<uuid:uuid>/teams/<int:event_team_id>/remove/", views.EventTeamRemove.as_view(), name="team-remove"),
]