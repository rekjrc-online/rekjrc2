document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.sponsor-link').forEach(el => {
    el.addEventListener('click', async (event) => {
      event.preventDefault();
      const sponsorId = el.dataset.sponsorId;

      try {
        const response = await fetch(`/sponsors/${sponsorId}/click/`, {
          method: 'POST',
          headers: {
            'X-CSRFToken': getCookie('csrftoken'),
          },
        });
        const data = await response.json();
        if (data.redirect_url) {
          window.open(data.redirect_url, '_blank');
        }
      } catch (err) {
        console.error('Error logging sponsor click:', err);
      }
    });
  });
});

// Helper to read Django CSRF token cookie
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
}

function recordSponsorClick(sponsorId, url) {
    fetch(`/sponsors/${sponsorId}/click/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
        },
    })
    .then(() => {
        window.open(url, '_blank');
    })
    .catch(err => {
        console.error('Error logging click:', err);
        window.open(url, '_blank'); // still open even if logging fails
    });
}
