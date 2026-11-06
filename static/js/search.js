/**
 * MOODFLIX - SEARCH JAVASCRIPT
 * Live search suggestions, debounced fetch, and dropdown navigation
 */

document.addEventListener('DOMContentLoaded', () => {
  const searchInput = document.getElementById('mainSearchInput');
  const searchDropdown = document.getElementById('liveSearchDropdown');
  const clearBtn = document.getElementById('searchClearBtn');

  if (!searchInput || !searchDropdown) return;

  let debounceTimer = null;

  // Toggle clear button visibility
  function toggleClearButton() {
    if (clearBtn) {
      if (searchInput.value.trim().length > 0) {
        clearBtn.classList.add('visible');
      } else {
        clearBtn.classList.remove('visible');
      }
    }
  }

  // Clear button click
  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      searchInput.value = '';
      toggleClearButton();
      searchDropdown.innerHTML = '';
      searchDropdown.classList.remove('open');
      searchInput.focus();
    });
  }

  // Input event with debounce
  searchInput.addEventListener('input', (e) => {
    const query = e.target.value.trim();
    toggleClearButton();

    clearTimeout(debounceTimer);

    if (query.length < 2) {
      searchDropdown.innerHTML = '';
      searchDropdown.classList.remove('open');
      return;
    }

    debounceTimer = setTimeout(async () => {
      try {
        const response = await fetch(`/movies/search/?q=${encodeURIComponent(query)}`, {
          headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json'
          }
        });

        if (response.ok) {
          const data = await response.json();
          renderDropdown(data.results, query);
        }
      } catch (err) {
        console.error('Live search error:', err);
      }
    }, 280);
  });

  function renderDropdown(results, query) {
    if (!results || results.length === 0) {
      searchDropdown.innerHTML = `
        <div style="padding: 1rem; text-align: center; color: var(--text-muted); font-size: 0.9rem;">
          No titles found for "${query}"
        </div>
      `;
      searchDropdown.classList.add('open');
      return;
    }

    const html = results.map(item => {
      const url = item.media_type === 'tv' ? `/movies/tv/${item.id}/` : `/movies/movie/${item.id}/`;
      const poster = item.poster_url || '/static/images/fallback_poster.svg';
      const year = item.release_year ? `(${item.release_year})` : '';
      const typeBadge = item.media_type === 'tv' ? 'TV Series' : 'Movie';

      return `
        <a href="${url}" class="live-search-item">
          <img src="${poster}" alt="${item.title}" class="live-search-thumb" loading="lazy" />
          <div>
            <div class="live-search-title">${item.title} ${year}</div>
            <div class="live-search-sub">${typeBadge} &bull; Rating: ★ ${item.vote_average || 'N/A'}</div>
          </div>
        </a>
      `;
    }).join('');

    searchDropdown.innerHTML = html;
    searchDropdown.classList.add('open');
  }

  // Close dropdown on click outside
  document.addEventListener('click', (e) => {
    if (!searchInput.contains(e.target) && !searchDropdown.contains(e.target)) {
      searchDropdown.classList.remove('open');
    }
  });

  // Re-open if query exists on focus
  searchInput.addEventListener('focus', () => {
    if (searchInput.value.trim().length >= 2 && searchDropdown.children.length > 0) {
      searchDropdown.classList.add('open');
    }
  });
});

