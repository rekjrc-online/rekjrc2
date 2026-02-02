from django.test import TestCase
from django.urls import reverse

class PagesViewTests(TestCase):

    def test_privacy_view(self):
        url = reverse('pages:privacy')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "RekjRC Privacy Policy")
        self.assertContains(response, "<!-- privacy.html -->")
        self.assertTemplateUsed(response, 'pages/privacy.html')

    def test_terms_view(self):
        url = reverse('pages:terms')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "RekjRC Terms of Service")
        self.assertContains(response, "<!-- terms.html -->")
        self.assertTemplateUsed(response, 'pages/terms.html')

    def test_crawler_comp_view(self):
        url = reverse('pages:crawler_comp')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Crawler Comp App")
        self.assertContains(response, "<!-- privacy_crawler_comp.html -->")
        self.assertTemplateUsed(response, 'pages/privacy_crawler_comp.html')

    def test_support_view(self):
        url = reverse('pages:support')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Frequently Asked Questions")
        self.assertContains(response, "<!-- support.html -->")
        self.assertTemplateUsed(response, 'pages/support.html')
