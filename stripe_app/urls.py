from django.urls import path

from .views import stripe_webhook

app_name = 'stripe_app'

urlpatterns = [
    # Each store's own Stripe dashboard needs a webhook pointed at its own
    # /stripe/webhook/<store.pk>/ -- see stripe_app.views.stripe_webhook.
    path("webhook/<int:store_pk>/", stripe_webhook, name="webhook"),
]
