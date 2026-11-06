from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from recommendations.engine import MoodRecommendationEngine, MOOD_DEFINITIONS
from recommendations.models import MoodHistory

@override_settings(
    TMDB_API_KEY='',
    TMDB_READ_ACCESS_TOKEN='',
    TMDB_API_READ_ACCESS_TOKEN='',
)
class RecommendationsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='moodtester',
            email='mood@example.com',
            password='TestPassword123!'
        )

    def test_mood_selection_page_loads(self):
        response = self.client.get(reverse('recommendations:mood_selection'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Select Your Emotional State")
        for mood in ['Happy', 'Sad', 'Relaxed', 'Stressed', 'Adventurous', 'Romantic']:
            self.assertContains(response, mood)

    def test_mood_recommendation_engine_happy(self):
        result = MoodRecommendationEngine.recommend('happy')
        self.assertEqual(result['mood']['name'], 'Happy')
        self.assertTrue(len(result['recommendations']) > 0)
        for item in result['recommendations']:
            self.assertIn('relevance_score', item)

    def test_mood_recommendation_engine_adventurous(self):
        result = MoodRecommendationEngine.recommend('adventurous')
        self.assertEqual(result['mood']['name'], 'Adventurous')
        self.assertTrue(len(result['recommendations']) > 0)

    def test_mood_recommendation_engine_romantic(self):
        result = MoodRecommendationEngine.recommend('romantic')
        self.assertEqual(result['mood']['name'], 'Romantic')
        self.assertTrue(len(result['recommendations']) > 0)

    def test_mood_recommendation_engine_sad(self):
        result = MoodRecommendationEngine.recommend('sad')
        self.assertEqual(result['mood']['name'], 'Sad')

    def test_mood_recommendation_engine_relaxed(self):
        result = MoodRecommendationEngine.recommend('relaxed')
        self.assertEqual(result['mood']['name'], 'Relaxed')

    def test_mood_recommendation_engine_stressed(self):
        result = MoodRecommendationEngine.recommend('stressed')
        self.assertEqual(result['mood']['name'], 'Stressed')

    def test_invalid_mood_fallback(self):
        result = MoodRecommendationEngine.recommend('completely_unknown_mood')
        self.assertEqual(result['mood']['slug'], 'happy')

    def test_mood_history_recorded_for_authenticated_user(self):
        self.client.login(username='moodtester', password='TestPassword123!')
        response = self.client.get(reverse('recommendations:mood_results', kwargs={'mood_slug': 'adventurous'}))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(MoodHistory.objects.filter(user=self.user, selected_mood='adventurous').exists())

    def test_mood_history_not_recorded_for_anonymous_user(self):
        initial_count = MoodHistory.objects.count()
        response = self.client.get(reverse('recommendations:mood_results', kwargs={'mood_slug': 'romantic'}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(MoodHistory.objects.count(), initial_count)
