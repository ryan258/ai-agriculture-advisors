(() => {
    let timer;
    function updateRetryButtons() {
        let waiting = false;
        document.querySelectorAll('button[data-retry-at]').forEach(button => {
            const seconds = Math.max(0, Math.ceil(Number(button.dataset.retryAt) - Date.now() / 1000));
            if (seconds) {
                waiting = true;
                button.disabled = true;
                button.dataset.waiting = 'true';
                const status = document.getElementById('roundtable-retry-status');
                if (status) status.textContent = `Retry available in ${seconds} seconds. Your completed answers are kept.`;
            } else if (button.dataset.waiting) {
                button.disabled = false;
                delete button.dataset.waiting;
                const status = document.getElementById('roundtable-retry-status');
                if (status) status.textContent = 'Ready to retry. Your completed answers will stay as written.';
            }
        });
        if (!waiting && timer) { clearInterval(timer); timer = undefined; }
        if (waiting && !timer) timer = setInterval(updateRetryButtons, 1000);
    }
    document.body.addEventListener('htmx:afterSwap', updateRetryButtons);
    document.body.addEventListener('htmx:responseError', event => {
        const status = document.getElementById('roundtable-retry-status');
        if (status && event.detail.xhr.status === 429) {
            status.textContent = 'Too many requests. Your answers are kept; try again shortly.';
        }
    });
    updateRetryButtons();
})();
