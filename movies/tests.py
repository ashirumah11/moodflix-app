from django.test import TestCase, Client, override_settings
from django.urls import reverse
from unittest.mock import patch
from movies import tmdb
from movies import services

@override_settings(
    TMDB_API_KEY='',
    TMDB_READ_ACCESS_TOKEN='',
    TMDB_API_READ_ACCESS_TOKEN='',
)
class MoviesTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_home_view_loads(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "How are you feeling today?")
        self.assertContains(response, "Trending Movies")

    def test_discover_view_loads(self):
        response = self.client.get(reverse('movies:discover'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Discover Catalog")

    def test_trending_view_loads(self):
        response = self.client.get(reverse('movies:trending'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Trending Entertainment")

    def test_search_view_get(self):
        response = self.client.get(reverse('movies:search'), {'q': 'Inception'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Inception")

    def test_search_view_ajax(self):
        response = self.client.get(
            reverse('movies:search'),
            {'q': 'Totoro'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('results', data)
        self.assertTrue(any('Totoro' in r['title'] for r in data['results']))

    def test_movie_detail_view(self):
        response = self.client.get(reverse('movies:movie_detail', kwargs={'tmdb_id': 104}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Interstellar")

    def test_tv_detail_view(self):
        response = self.client.get(reverse('movies:tv_detail', kwargs={'tmdb_id': 201}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ted Lasso")

    def test_tmdb_image_url_fallback(self):
        url = tmdb.get_image_url(None)
        self.assertIn("fallback_poster.svg", url)
        backdrop_url = tmdb.get_image_url(None, is_backdrop=True)
        self.assertIn("fallback_backdrop.svg", backdrop_url)

    def test_tmdb_genre_resolution(self):
        genres = tmdb.get_movie_genres()
        self.assertTrue(len(genres) > 0)
        names = [g['name'] for g in genres]
        self.assertIn('Comedy', names)
        self.assertIn('Drama', names)

    def test_trailer_selection_prefers_an_official_youtube_trailer(self):
        videos = [
            {'site': 'YouTube', 'type': 'Trailer', 'official': False, 'key': 'general-key'},
            {'site': 'YouTube', 'type': 'Trailer', 'official': True, 'key': 'official-key'},
            {'site': 'YouTube', 'type': 'Trailer', 'official': True, 'key': 'bad key!'},
        ]
        self.assertEqual(tmdb.extract_youtube_trailer(videos), 'official-key')

    def test_trailer_endpoint_returns_a_friendly_missing_trailer_response(self):
        with patch('movies.views.tmdb.get_trailer', return_value=None):
            response = self.client.get(reverse('movies:movie_trailer', kwargs={'media_type': 'movie', 'tmdb_id': 123}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'not_found')
        self.assertIn('no trailer', response.json()['message'].lower())

    def test_trailer_endpoint_rejects_an_invalid_media_type(self):
        response = self.client.get('/movies/trailer/person/123/')
        self.assertEqual(response.status_code, 400)

    def test_invalid_rating_filter_does_not_break_discovery(self):
        response = self.client.get(reverse('movies:discover'), {'rating': 'not-a-number'})
        self.assertEqual(response.status_code, 200)
