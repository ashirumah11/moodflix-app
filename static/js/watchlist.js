/**
 * MOODFLIX - WATCHLIST JAVASCRIPT
 * AJAX Watchlist toggling, watched state management, and badge count updates
 */

document.addEventListener('DOMContentLoaded', () => {
  // Helper: Retrieve CSRF token from cookies
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  const csrfToken = getCookie('csrftoken') || (document.querySelector('[name=csrfmiddlewaretoken]')?.value);

  // Helper: Update all watchlist badges on the page
  function updateWatchlistBadge(count) {
    const badges = document.querySelectorAll('.watchlist-nav-btn .badge-count, .watchlist-count-display');
    badges.forEach((badge) => {
      badge.textContent = count;
      if (count > 0) {
        badge.style.display = 'inline-flex';
      } else {
        badge.style.display = 'none';
      }
    });
  }

  // 1. AJAX Watchlist Toggle Buttons
  document.addEventListener('click', async (e) => {
    const btn = e.target.closest('.watchlist-ajax-btn');
    if (!btn) return;

    e.preventDefault();

    const tmdbId = btn.dataset.tmdbId;
    const mediaType = btn.dataset.mediaType || 'movie';
    const title = btn.dataset.title || 'Movie';
    const posterPath = btn.dataset.posterPath || '';
    const backdropPath = btn.dataset.backdropPath || '';
    const voteAverage = btn.dataset.voteAverage || 0;
    const releaseDate = btn.dataset.releaseDate || '';

    // If user is not authenticated, prompt to login
    if (!btn.dataset.authenticated || btn.dataset.authenticated === 'false') {
      window.location.href = `/accounts/login/?next=${encodeURIComponent(window.location.pathname)}`;
      return;
    }

    try {
      btn.style.pointerEvents = 'none';
      btn.style.opacity = '0.7';

      const response = await fetch('/watchlist/toggle/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
          'X-Requested-With': 'XMLHttpRequest',
        },
        body: JSON.stringify({
          tmdb_id: tmdbId,
          media_type: mediaType,
          title: title,
          poster_path: posterPath,
          backdrop_path: backdropPath,
          vote_average: voteAverage,
          release_date: releaseDate,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        const isInWatchlist = data.in_watchlist;

        // Toggle state class and icon across all buttons for this movie on the page
        const matchingButtons = document.querySelectorAll(`[data-tmdb-id="${tmdbId}"]`);
        matchingButtons.forEach((b) => {
          if (isInWatchlist) {
            b.classList.add('active');
            b.setAttribute('title', 'Remove from Watchlist');
            b.innerHTML = '<span class="icon">✓</span>';
          } else {
            b.classList.remove('active');
            b.setAttribute('title', 'Add to Watchlist');
            b.innerHTML = '<span class="icon">+</span>';
          }
        });

        // Update badge count
        if (data.watchlist_count !== undefined) {
          updateWatchlistBadge(data.watchlist_count);
        }

        if (window.showToast) {
          window.showToast(data.message, isInWatchlist ? 'success' : 'info');
        }
      } else {
        if (window.showToast) {
          window.showToast('Unable to update watchlist.', 'error');
        }
      }
    } catch (err) {
      console.error('Watchlist error:', err);
    } finally {
      btn.style.pointerEvents = '';
      btn.style.opacity = '';
    }
  });

  // 2. Watchlist Page - Toggle Watched Status
  document.addEventListener('click', async (e) => {
    const watchedBtn = e.target.closest('.toggle-watched-btn');
    if (!watchedBtn) return;

    e.preventDefault();
    const itemId = watchedBtn.dataset.itemId;

    try {
      const response = await fetch(`/watchlist/toggle-watched/${itemId}/`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': csrfToken,
          'X-Requested-With': 'XMLHttpRequest',
        },
      });

      if (response.ok) {
        const data = await response.json();
        const card = document.getElementById(`watchlist-item-${itemId}`);
        if (card) {
          const statusBadge = card.querySelector('.watched-status-indicator');
          if (statusBadge) {
            if (data.watched) {
              statusBadge.textContent = 'Watched';
              statusBadge.className = 'watched-status-indicator watched';
              watchedBtn.textContent = 'Mark Unwatched';
            } else {
              statusBadge.textContent = 'Unwatched';
              statusBadge.className = 'watched-status-indicator unwatched';
              watchedBtn.textContent = 'Mark Watched';
            }
          }
        }
        if (window.showToast) {
          window.showToast(data.message, 'success');
        }
      }
    } catch (err) {
      console.error('Toggle watched error:', err);
    }
  });

  // 3. Watchlist Page - Remove Item Button
  document.addEventListener('click', async (e) => {
    const removeBtn = e.target.closest('.remove-watchlist-btn');
    if (!removeBtn) return;

    e.preventDefault();
    if (!confirm('Remove this title from your watchlist?')) return;

    const itemId = removeBtn.dataset.itemId;

    try {
      const response = await fetch(`/watchlist/remove/${itemId}/`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': csrfToken,
          'X-Requested-With': 'XMLHttpRequest',
        },
      });

      if (response.ok) {
        const data = await response.json();
        const card = document.getElementById(`watchlist-item-${itemId}`);
        if (card) {
          card.style.transition = 'all 0.3s ease';
          card.style.opacity = '0';
          card.style.transform = 'scale(0.9)';
          setTimeout(() => {
            card.remove();
            // If empty, reload or show empty state
            const remaining = document.querySelectorAll('.watchlist-card-item');
            if (remaining.length === 0) {
              window.location.reload();
            }
          }, 300);
        }
        if (data.watchlist_count !== undefined) {
          updateWatchlistBadge(data.watchlist_count);
        }
        if (window.showToast) {
          window.showToast(data.message, 'info');
        }
      }
    } catch (err) {
      console.error('Remove error:', err);
    }
  });
});

