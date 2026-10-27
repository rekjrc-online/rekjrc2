// static/prices.js -- auto-save for templates/products/manage_prices.html.
// Each .price-input POSTs to its data-url on change (blur) or Enter, only
// when the value differs from the last saved value (data-saved).
document.addEventListener('DOMContentLoaded', function() {
    const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
    if (!csrfInput) return;
    const csrftoken = csrfInput.value;

    function setStatus(input, text, color) {
        const status = input.closest('tr').querySelector('.price-status');
        if (!status) return;
        status.textContent = text;
        status.style.color = color || '';
    }

    function save(input) {
        const value = input.value.trim();
        if (value === input.dataset.saved) {
            setStatus(input, '');
            return;
        }
        setStatus(input, 'Saving...');
        const body = new URLSearchParams({ price: value });

        fetch(input.dataset.url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'Accept': 'application/json',
            },
            body: body,
        })
        .then(response => response.json().catch(() => ({ ok: false, error: 'Server error (' + response.status + ').' })))
        .then(data => {
            if (data.ok) {
                input.value = data.price;
                input.dataset.saved = data.price;
                setStatus(input, 'Saved ✓', 'limegreen');
            } else {
                // Leave the typed value in place so it can be corrected.
                setStatus(input, data.error || 'Not saved.', 'red');
            }
        })
        .catch(() => setStatus(input, 'Network error -- not saved.', 'red'));
    }

    document.querySelectorAll('.price-input').forEach(input => {
        input.addEventListener('change', () => save(input));
        input.addEventListener('keydown', e => {
            if (e.key === 'Enter') {
                e.preventDefault();
                input.blur();  // fires 'change' if the value changed
            }
            if (e.key === 'Escape') {
                input.value = input.dataset.saved;
                setStatus(input, '');
            }
        });
    });

    // Warn before leaving with a value that failed to save or is mid-edit.
    window.addEventListener('beforeunload', e => {
        const dirty = Array.from(document.querySelectorAll('.price-input'))
            .some(i => i.value.trim() !== i.dataset.saved);
        if (dirty) {
            e.preventDefault();
            e.returnValue = '';
        }
    });
});
