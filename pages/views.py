from django.views.generic import TemplateView

class PrivacyView(TemplateView):
    template_name = 'pages/privacy.html'

class TermsView(TemplateView):
    template_name = 'pages/terms.html'

class PrivacyViewCrawlercomp(TemplateView):
    template_name = 'pages/privacy_crawler_comp.html'

class SupportView(TemplateView):
    template_name = 'pages/support.html'