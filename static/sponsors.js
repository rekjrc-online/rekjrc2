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

// Fire-and-forget click log. The <a target="_blank"> opens the sponsor site
// itself, synchronously, so popup blockers don't eat it the way a
// window.open() after an awaited fetch would. keepalive lets the request
// finish even if the page navigates.
function recordSponsorClick(sponsorId) {
    fetch(`/sponsors/${sponsorId}/click/`, {
        method: 'POST',
        keepalive: true,
        headers: {
            'X-CSRFToken': getCookie('csrftoken') || '',
        },
    }).catch(err => console.error('Error logging sponsor click:', err));
}
