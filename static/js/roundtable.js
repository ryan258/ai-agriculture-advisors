(() => {
    let timer;
    function updateRetryButtons() {
        let waiting = false;
        document.querySelectorAll('button[data-retry-at]').forEach(button => {
            const seconds = Math.max(0, Math.ceil(Number(button.dataset.retryAt) - Date.now() / 1000));
            const status = document.getElementById(button.dataset.statusId || 'roundtable-retry-status');
            const countdown = document.getElementById(button.dataset.countdownId || 'roundtable-retry-countdown');
            if (seconds) {
                waiting = true;
                button.disabled = true;
                if (status && !button.dataset.waiting) status.textContent = 'A provider minimum wait is active. Your completed answers are kept.';
                button.dataset.waiting = 'true';
                if (countdown) countdown.textContent = `Retry available in ${seconds} seconds.`;
            } else if (button.dataset.waiting) {
                button.disabled = Boolean(button.dataset.requestPending);
                delete button.dataset.waiting;
                if (status) status.textContent = 'Ready to retry. Your completed answers will stay as written.';
                if (countdown) countdown.textContent = '';
            }
        });
        if (!waiting && timer) { clearInterval(timer); timer = undefined; }
        if (waiting && !timer) timer = setInterval(updateRetryButtons, 1000);
    }
    document.body.addEventListener('htmx:afterSwap', updateRetryButtons);
    document.body.addEventListener('htmx:responseError', event => {
        if (!event.detail.target || event.detail.target.id !== 'response') return;
        const status = document.getElementById('roundtable-retry-status');
        if (status && event.detail.xhr.status === 429) {
            status.textContent = 'Too many requests. Your answers are kept; try again shortly.';
        }
    });
    updateRetryButtons();
})();
