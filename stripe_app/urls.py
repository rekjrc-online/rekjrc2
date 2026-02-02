from django.urls import path
from django.views.generic import TemplateView
from .views import CheckoutView, StripeWebhookView, PaymentSuccessView, PaymentCancelView

app_name = 'stripe'

urlpatterns = [
    path("checkout/<slug:product_slug>/", CheckoutView.as_view(), name="checkout"),
    path("webhook/", StripeWebhookView.as_view(), name="webhook"),
    path("success/", PaymentSuccessView.as_view(), name="success"),
    path("cancel/", PaymentCancelView.as_view(), name="cancel"),
    path("products/", TemplateView.as_view(template_name="stripe_app/products.html"), name="products"),
]
