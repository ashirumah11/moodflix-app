from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from watchlist.models import Watchlist

class WatchlistTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(
            username='user_alice',
            email='alice@example.com',
            password='Password123!'
        )
        self.user2 = User.objects.create_user(
            username='user_bob',
            email='bob@example.com',
            password='Password123!'
        )

    def test_watchlist_requires_login(self):
        response = self.client.get(reverse('watchlist:index'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_watchlist_add_movie(self):
        self.client.login(username='user_alice', password='Password123!')
        response = self.client.post(reverse('watchlist:toggle'), {
            'tmdb_id': 101,
            'media_type': 'movie',
            'title': 'Everything Everywhere All at Once',
            'poster_path': '/poster.jpg',
            'vote_average': '8.0',
            'release_date': '2022-03-24',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Watchlist.objects.filter(user=self.user1, tmdb_id=101).exists())

    def test_watchlist_prevent_duplicate_and_toggles(self):
        self.client.login(username='user_alice', password='Password123!')
        # First call adds
        self.client.post(reverse('watchlist:toggle'), {
            'tmdb_id': 102,
            'media_type': 'movie',
            'title': 'Amélie',
        })
        self.assertEqual(Watchlist.objects.filter(user=self.user1, tmdb_id=102).count(), 1)

        # Second call removes (toggles off)
        self.client.post(reverse('watchlist:toggle'), {
            'tmdb_id': 102,
            'media_type': 'movie',
            'title': 'Amélie',
        })
        self.assertEqual(Watchlist.objects.filter(user=self.user1, tmdb_id=102).count(), 0)

    def test_watchlist_toggle_watched(self):
        self.client.login(username='user_alice', password='Password123!')
        item = Watchlist.objects.create(
            user=self.user1,
            tmdb_id=103,
            media_type='movie',
            title='Paddington 2',
            watched=False
        )
        response = self.client.post(reverse('watchlist:toggle_watched', kwargs={'item_id': item.id}))
        self.assertEqual(response.status_code, 302)
        item.refresh_from_db()
        self.assertTrue(item.watched)

    def test_user_data_isolation_cannot_access_other_user_watchlist(self):
        """
        Verify that User B cannot mark as watched or remove User A's watchlist item.
        """
        item_alice = Watchlist.objects.create(
            user=self.user1,
            tmdb_id=104,
            media_type='movie',
            title='Interstellar',
            watched=False
        )

        # Bob logs in and tries to toggle watched on Alice's item
        self.client.login(username='user_bob', password='Password123!')
        response_watched = self.client.post(reverse('watchlist:toggle_watched', kwargs={'item_id': item_alice.id}))
        self.assertEqual(response_watched.status_code, 404)

        item_alice.refresh_from_db()
        self.assertFalse(item_alice.watched)  # Status should remain unchanged

        # Bob tries to delete Alice's item
        response_delete = self.client.post(reverse('watchlist:remove', kwargs={'item_id': item_alice.id}))
        self.assertEqual(response_delete.status_code, 404)

        self.assertTrue(Watchlist.objects.filter(id=item_alice.id).exists())  # Item remains intact

    def test_watchlist_index_displays_only_own_items(self):
        Watchlist.objects.create(user=self.user1, tmdb_id=104, title="Alice Secret Film")
        Watchlist.objects.create(user=self.user2, tmdb_id=105, title="Bob Favorite Film")

        self.client.login(username='user_alice', password='Password123!')
        response = self.client.get(reverse('watchlist:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alice Secret Film")
        self.assertNotContains(response, "Bob Favorite Film")
