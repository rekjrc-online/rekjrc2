from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import path, include
from django.views.generic import TemplateView
from posts import views

def custom_404(request, exception):
    return render(request, "pages/404.html", status=404)

def custom_500(request):
    return render(request, "pages/500.html", status=500)

urlpatterns = [
    path('admin/', admin.site.urls, name='admin'),
    path('', views.homepage, name='homepage'),
    path("robots.txt",lambda request: HttpResponse("User-agent: *\nDisallow:\n",content_type="text/plain; charset=utf-8"),),
    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),
    path('pages/', include(('pages.urls', 'pages'), namespace='pages')),
    path('posts/', include(('posts.urls', 'posts'), namespace='posts')),
    path('chat/', include(('chat_app.urls', 'chat_app'), namespace='chat')),
    path('okta/', include('mozilla_django_oidc.urls')),

    path('u/', include(('urls_app.urls', 'urls_app'), namespace='urls_app')),
    # path('sponsors/', include(('sponsors.urls', 'sponsors'), namespace='sponsors')),
    # path('stripe/', include(('stripe_app.urls', 'stripe_app'), namespace='stripe')),
    # path('support/', include(('support.urls', 'support'), namespace='support')),

    path('builds/', include(('builds.urls', 'builds'), namespace='builds')),
    path('clubs/', include(('clubs.urls', 'clubs'), namespace='clubs')),
    path('drivers/', include(('drivers.urls', 'drivers'), namespace='drivers')),
    path('events/', include(('events.urls', 'events'), namespace='events')),
    path('locations/', include(('locations.urls', 'locations'), namespace='locations')),
    path('races/', include(('races.urls', 'races'), namespace='races')),
    path('stores/', include(('stores.urls', 'stores'), namespace='stores')),
    path('teams/', include(('teams.urls', 'teams'), namespace='teams')),
    path('tracks/', include(('tracks.urls', 'tracks'), namespace='tracks')),

    path('dragrace/', include(('dragrace.urls', 'dragrace'), namespace='dragrace')),
    path('crawler/', include(('crawler.urls', 'crawler'), namespace='crawler')),
    path('stopwatch/', include(('stopwatch.urls', 'stopwatch'), namespace='stopwatch')),
    path('judged/', include(('judged.urls', 'judged'), namespace='judged')),
    path('laprace/', include(('laprace.urls', 'laprace'), namespace='laprace')),
    path('longjump/', include(('longjump.urls', 'longjump'), namespace='longjump')),
    path('topspeed/', include(('topspeed.urls', 'topspeed'), namespace='topspeed')),
    path('roundrobin/', include(('roundrobin.urls', 'roundrobin'), namespace='roundrobin')),
    path('swiss/', include(('swiss.urls', 'swiss'), namespace='swiss')),

    path("api/accounts/", include(("accounts.api.urls","accounts_api"), namespace="accounts_api")),
    path("api/builds/", include(("builds.api.urls","builds_api"), namespace="builds_api")),
    path("api/clubs/", include(("clubs.api.urls","clubs_api"), namespace="clubs_api")),
    path("api/drivers/", include(("drivers.api.urls","drivers_api"), namespace="drivers_api")),
    path("api/events/", include(("events.api.urls","events_api"), namespace="events_api")),
    path("api/locations/", include(("locations.api.urls","locations_api"), namespace="locations_api")),
    path("api/posts/", include(("posts.api.urls","posts_api"), namespace="posts_api")),
    path("api/races/", include(("races.api.urls","races_api"), namespace="races_api")),
    path("api/stores/", include(("stores.api.urls","stores_api"), namespace="stores_api")),
    path("api/teams/", include(("teams.api.urls","teams_api"), namespace="teams_api")),
    path("api/tracks/", include(("tracks.api.urls","tracks_api"), namespace="tracks_api"))
]

handler404 = 'rekjrc.urls.custom_404'
handler500 = 'rekjrc.urls.custom_500'

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
