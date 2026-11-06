/**
 * MOODFLIX - MAIN JAVASCRIPT
 * Navigation, Navbar Scroll, YouTube Trailer Modal, Carousels & Toast Alerts
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Mobile Menu Toggle
  const mobileToggle = document.getElementById('mobileMenuToggle');
  const navLinks = document.getElementById('navLinks');

  if (mobileToggle && navLinks) {
    mobileToggle.addEventListener('click', () => {
      navLinks.classList.toggle('mobile-open');
      const isExpanded = navLinks.classList.contains('mobile-open');
      mobileToggle.setAttribute('aria-expanded', isExpanded);
    });

    // Close when clicking outside
    document.addEventListener('click', (e) => {
      if (!mobileToggle.contains(e.target) && !navLinks.contains(e.target)) {
        navLinks.classList.remove('mobile-open');
      }
    });
  }

  // 2. Navbar Background on Scroll
  const siteHeader = document.querySelector('.site-header');
  if (siteHeader) {
    window.addEventListener('scroll', () => {
      if (window.scrollY > 40) {
        siteHeader.classList.add('scrolled');
      } else {
        siteHeader.classList.remove('scrolled');
      }
    }, { passive: true });
  }

  // 3. Toast Messages Dismiss
  const toastAlerts = document.querySelectorAll('.toast-alert');
  toastAlerts.forEach((toast) => {
    // Auto dismiss after 4.5 seconds
    const timer = setTimeout(() => {
      dismissToast(toast);
    }, 4500);

    const closeBtn = toast.querySelector('.toast-close-btn');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        clearTimeout(timer);
        dismissToast(toast);
      });
    }
  });

  function dismissToast(element) {
    element.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
    element.style.opacity = '0';
    element.style.transform = 'translateX(50px)';
    setTimeout(() => {
      element.remove();
    }, 300);
  }

  // 4. Robust YouTube Trailer Modal Controller
  const trailerModal = document.getElementById('trailerModal');
  const trailerFrame = document.getElementById('trailerIframe');
  const trailerTitle = document.getElementById('trailerModalTitle');
  const trailerExternalLink = document.getElementById('trailerExternalLink');
  const trailerLoading = document.getElementById('trailerLoading');
  const trailerErrorNotice = document.getElementById('trailerErrorNotice');
  const trailerErrorMessage = document.getElementById('trailerErrorMessage');
  const closeTrailerBtn = document.getElementById('closeTrailerBtn');
  const trailerDismissBtn = document.getElementById('trailerDismissBtn');

  const closeModal = () => {
    if (!trailerModal) return;
    trailerModal.classList.remove('open');
    if (trailerFrame) {
      trailerFrame.src = '';
    }
    document.body.style.overflow = '';
    if (trailerLoading) trailerLoading.style.display = 'none';
    if (trailerErrorNotice) trailerErrorNotice.style.display = 'none';
    if (trailerExternalLink) trailerExternalLink.style.display = 'none';
  };

  if (trailerModal) {
    if (closeTrailerBtn) closeTrailerBtn.addEventListener('click', closeModal);
    if (trailerDismissBtn) trailerDismissBtn.addEventListener('click', closeModal);

    trailerModal.addEventListener('click', (e) => {
      if (e.target === trailerModal) {
        closeModal();
      }
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && trailerModal.classList.contains('open')) {
        closeModal();
      }
    });

    // Delegated click handler for all trailer buttons
    document.addEventListener('click', async (e) => {
      const btn = e.target.closest('.open-trailer-btn, [data-trailer-key], [data-trailer-id]');
      if (!btn) return;

      e.preventDefault();
      e.stopPropagation();

      const key = btn.getAttribute('data-trailer-key');
      const tmdbId = btn.getAttribute('data-trailer-id') || btn.getAttribute('data-tmdb-id');
      const mediaType = btn.getAttribute('data-media-type') || 'movie';
      const title = btn.getAttribute('data-title') || 'Official Trailer';

      if (trailerTitle) {
        trailerTitle.textContent = title.toLowerCase().includes('trailer') ? title : `${title} — Trailer`;
      }

      // Reset modal view states
      if (trailerLoading) trailerLoading.style.display = 'none';
      if (trailerErrorNotice) trailerErrorNotice.style.display = 'none';
      if (trailerExternalLink) trailerExternalLink.style.display = 'none';
      if (trailerFrame) trailerFrame.style.display = 'block';

      // Open modal & lock scroll
      trailerModal.classList.add('open');
      document.body.style.overflow = 'hidden';

      // Scenario A: Video key is already known
      if (key && key.trim() !== '') {
        const cleanKey = key.trim();
        trailerFrame.src = `https://www.youtube.com/embed/${cleanKey}?autoplay=1&rel=0`;
        if (trailerExternalLink) {
          trailerExternalLink.href = `https://www.youtube.com/watch?v=${cleanKey}`;
          trailerExternalLink.style.display = 'inline-flex';
        }
        return;
      }

      // Scenario B: Video key needs to be fetched on demand by TMDB ID
      if (tmdbId) {
        if (trailerLoading) trailerLoading.style.display = 'flex';
        if (trailerFrame) trailerFrame.style.display = 'none';

        try {
          const res = await fetch(`/movies/trailer/${mediaType}/${tmdbId}/`);
          if (!res.ok) {
            throw new Error(`Trailer request failed with status ${res.status}`);
          }
          const data = await res.json();

          if (trailerLoading) trailerLoading.style.display = 'none';

          if (data.status === 'success' && data.has_trailer && data.key) {
            if (trailerFrame) {
              trailerFrame.style.display = 'block';
              trailerFrame.src = data.embed_url;
            }
            if (trailerExternalLink) {
              trailerExternalLink.href = data.watch_url;
              trailerExternalLink.style.display = 'inline-flex';
            }
          } else {
            // No trailer found
            if (trailerFrame) trailerFrame.style.display = 'none';
            if (trailerErrorNotice) {
              trailerErrorNotice.style.display = 'flex';
              if (trailerErrorMessage) {
                trailerErrorMessage.textContent = data.message || 'Sorry, no trailer is currently available for this movie.';
              }
            }
            if (window.showToast) {
              window.showToast('Sorry, no trailer is currently available for this movie.', 'info');
            }
          }
        } catch (err) {
          console.error('Trailer fetch error:', err);
          if (trailerLoading) trailerLoading.style.display = 'none';
          if (trailerErrorNotice) {
            trailerErrorNotice.style.display = 'flex';
            if (trailerErrorMessage) {
              trailerErrorMessage.textContent = 'Unable to load trailer. Please try again.';
            }
          }
        }
      } else {
        if (trailerFrame) trailerFrame.style.display = 'none';
        if (trailerErrorNotice) {
          trailerErrorNotice.style.display = 'flex';
          if (trailerErrorMessage) {
            trailerErrorMessage.textContent = 'Sorry, no trailer is currently available for this movie.';
          }
        }
      }
    });
  }

  // 5. Carousel Scroll Buttons
  const carouselContainers = document.querySelectorAll('.carousel-container');
  carouselContainers.forEach((container) => {
    const track = container.querySelector('.carousel-track');
    const prevBtn = container.querySelector('.carousel-nav-prev');
    const nextBtn = container.querySelector('.carousel-nav-next');

    if (track && prevBtn && nextBtn) {
      const scrollStep = 320;
      prevBtn.addEventListener('click', () => {
        track.scrollBy({ left: -scrollStep, behavior: 'smooth' });
      });
      nextBtn.addEventListener('click', () => {
        track.scrollBy({ left: scrollStep, behavior: 'smooth' });
      });
    }
  });
});

/**
 * Global helper to show dynamic toast notifications
 */
window.showToast = function(message, type = 'info') {
  let container = document.querySelector('.messages-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'messages-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast-alert ${type}`;
  toast.innerHTML = `
    <span>${message}</span>
    <button class="toast-close-btn" aria-label="Close message">&times;</button>
  `;

  container.appendChild(toast);

  const closeBtn = toast.querySelector('.toast-close-btn');
  const timer = setTimeout(() => {
    toast.remove();
  }, 4500);

  closeBtn.addEventListener('click', () => {
    clearTimeout(timer);
    toast.remove();
  });
};
