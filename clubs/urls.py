from django.urls import path
from . import views

app_name = 'clubs'

urlpatterns = [
    path("", views.List_.as_view(), name="list"),
    path("<uuid:uuid>/", views.Detail_.as_view(), name="detail"),
    path("create/", views.Create_.as_view(), name="create"),

    path("<uuid:uuid>/edit/", views.Update_.as_view(), name="edit"),
    path("<uuid:uuid>/delete/", views.Delete_.as_view(), name="delete"),
    path("<uuid:uuid>/advanced/", views.Advanced_.as_view(), name="advanced"),

    path('<uuid:uuid>/locations/add/', views.ClubLocationAdd.as_view(), name='location-add'),
    path('<uuid:uuid>/locations/<int:club_location_id>/remove/', views.ClubLocationRemove.as_view(), name='location-remove'),

    path('<uuid:uuid>/members/add/', views.ClubMemberAdd.as_view(), name='member-add'),
    path('<uuid:uuid>/members/<int:club_member_id>/remove/', views.ClubMemberRemove.as_view(), name='member-remove'),

    path('<uuid:uuid>/teams/add/', views.ClubTeamAdd.as_view(), name='team-add'),
    path('<uuid:uuid>/teams/<int:club_team_id>/remove/', views.ClubTeamRemove.as_view(), name='team-remove'),
]