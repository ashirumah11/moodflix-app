/**
 * MOODFLIX - MOOD INTERACTION JAVASCRIPT
 * Dynamic card effects and mood selection handling
 */

document.addEventListener('DOMContentLoaded', () => {
  const moodCards = document.querySelectorAll('.mood-card');

  moodCards.forEach((card) => {
    // Subtle tilt & ripple feedback
    card.addEventListener('mouseenter', () => {
      card.style.transition = 'transform 0.25s cubic-bezier(0.16, 1, 0.3, 1)';
    });

    card.addEventListener('mouseleave', () => {
      card.style.transform = '';
    });

    // Provide immediate visual response on click
    card.addEventListener('click', (e) => {
      const href = card.getAttribute('href');
      if (href) {
        card.style.transform = 'scale(0.96)';
      }
    });
  });
});

