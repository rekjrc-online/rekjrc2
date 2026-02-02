document.addEventListener('DOMContentLoaded', () => {
    let page = window.SCROLL_CONFIG.startPage || 2;
    let loading = false;
    let hasMore = true;

    const feed = document.getElementById(window.SCROLL_CONFIG.feedId);
    const loadingIndicator = document.getElementById(window.SCROLL_CONFIG.loadingId);
    const endMessage = document.getElementById(window.SCROLL_CONFIG.endMessageId);

    if (!feed || !loadingIndicator || !endMessage) return;

    const observer = new IntersectionObserver(entries => {
        const entry = entries[0];
        if (entry.isIntersecting && !loading && hasMore) {
            loading = true;
            loadingIndicator.style.display = 'block';

            setTimeout(() => {
                fetch(`${window.SCROLL_CONFIG.fetchUrl}?page=${page}`, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
                    .then(response => response.json())
                    .then(data => {
                        if (!data.html || data.html.trim() === '') {
                            hasMore = false;
                            endMessage.style.display = 'block';
                        } else {
                            feed.insertAdjacentHTML('beforeend', data.html);
                            page += 1;
                            if (!data.has_next) {
                                hasMore = false;
                                endMessage.style.display = 'block';
                            }
                        }
                    })
                    .catch(err => console.error('Error fetching posts:', err))
                    .finally(() => {
                        loading = false;
                        if (!hasMore) loadingIndicator.style.display = 'none';
                    });
            }, 2000);  // <-- 2 seconds
        }
    }, { root: null, rootMargin: '0px', threshold: 0.1 });

    observer.observe(loadingIndicator);
});
