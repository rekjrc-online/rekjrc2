from django.contrib import admin
from .models import RoundRobinRace

@admin.register(RoundRobinRace)
class RoundRobinRaceAdmin(admin.ModelAdmin):
    list_display  = ('id', 'race_display', 'model1_display', 'model2_display', 'winner_display')
    search_fields = (
        'race__display_name',
        'model1__driver__display_name',
        'model2__driver__display_name',
        'winner__driver__display_name',
    )
    list_filter   = ('race',)
    ordering      = ('race__created_at', 'id')

    def race_display(self, obj):
        return str(obj.race)
    race_display.short_description = 'Race'

    def model1_display(self, obj):
        return str(obj.model1)
    model1_display.short_description = 'Lane 1'

    def model2_display(self, obj):
        return str(obj.model2)
    model2_display.short_description = 'Lane 2'

    def winner_display(self, obj):
        return str(obj.winner) if obj.winner else '–'
    winner_display.short_description = 'Winner'
