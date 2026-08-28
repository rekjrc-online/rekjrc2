document.addEventListener('DOMContentLoaded', function () {

    var page = 2;
    var loading = false;
    var hasMore = true;

    var feed = document.getElementById('feed');
    var loadingIndicator = document.getElementById('loading');
    var endMessage = document.getElementById('end-message');

    var observer = new IntersectionObserver(function (entries) {
        var entry = entries[0];

        if (!entry.isIntersecting) return;
        if (loading || !hasMore) return;

        loading = true;
        loadingIndicator.style.display = 'block';

        var xhr = new XMLHttpRequest();
        xhr.open('GET', '?page=' + page, true);
        xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');

        xhr.onreadystatechange = function () {
            if (xhr.readyState !== 4) return;

            loading = false;

            if (xhr.status !== 200) return;

            var data = JSON.parse(xhr.responseText);

            if (!data.html || !data.html.trim()) {
                hasMore = false;
            } else {
                feed.insertAdjacentHTML('beforeend', data.html);
                page++;
                if (data.end) {
                    hasMore = false;
                }
            }

            // Only hide the sentinel once there truly is no more to load --
            // an IntersectionObserver stops firing for a target once it has
            // display:none (no box to re-intersect), so hiding it after every
            // fetch (as this used to do unconditionally) silently killed
            // pagination after the very first extra page loaded.
            if (!hasMore) {
                loadingIndicator.style.display = 'none';
                endMessage.style.display = 'block';
            }
        };

        xhr.send();

    }, {
        root: null,
        rootMargin: '0px',
        threshold: 0.1
    });

    observer.observe(loadingIndicator);

});
