document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.like-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log(this.dataset);
            const post_uuid = this.dataset.postId;
            const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
            if (!csrfInput) return;
            const csrftoken = csrfInput.value;

            fetch(`/posts/like-ajax/${post_uuid}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                    'Accept': 'application/json',
                },
            })
            .then(response => response.json())
            .then(data => {
                const metricsDiv = document.querySelector(`.metrics[data-post-id="${post_uuid}"]`);
                if (!metricsDiv) {
                    console.error("Metrics div not found for post", post_uuid);
                    return;
                }
                const likeCount = metricsDiv.querySelector('.like-count');
                if (!likeCount) {
                    console.error("Like count element not found inside metrics div");
                    return;
                }
                likeCount.textContent = data.likes_count;

                const heart = btn.querySelector('.heart');
                if (heart) {
                    heart.textContent = data.liked ? '❤️' : '🤍';
                    // Add pop animation class
                    heart.classList.add('liked');
                    heart.addEventListener('animationend', () => {
                        heart.classList.remove('liked');
                    }, { once: true });
                } else {
                    btn.textContent = data.liked ? '❤️' : '🤍';
                }
            })
            .catch(err => console.error("AJAX error:", err));
        });
    });
});
