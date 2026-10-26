// Local convenience controls; saved content is never submitted to an advisor here.
(() => {
    const returnKey = 'ai-advisors-last-result';
    const validId = value => typeof value === 'string' && /^[a-zA-Z0-9_-]{1,80}$/.test(value);
    let returnId = '';
    let activeRequest = null;
    let elapsedTimer;
    let startedAt = 0;
    let waitingText = '';
    let disabledButtons = [];
    let resumeRefresh;
    const savingNotes = new Map();

    try {
        const savedId = localStorage.getItem(returnKey);
        if (validId(savedId)) returnId = savedId;
        else if (savedId) localStorage.removeItem(returnKey);
    } catch (_) { /* History remains available when browser storage is unavailable. */ }

    function refreshResume() {
        const panel = document.getElementById('resumePanel');
        if (panel && window.htmx) {
            const url = returnId ? `/resume?result_id=${encodeURIComponent(returnId)}` : '/resume';
            window.htmx.ajax('GET', url, {target: panel, source: panel, swap: 'innerHTML'});
        }
    }

    function scheduleResumeRefresh() {
        clearTimeout(resumeRefresh);
        resumeRefresh = setTimeout(refreshResume, 0);
    }

    function lockNotes(detail) {
        const notes = detail.elt && detail.elt.closest('.personal-notes');
        if (!notes || savingNotes.has(detail.xhr)) return;
        const fields = Array.from(notes.querySelectorAll('input:not([type="hidden"]), textarea, select'), field => ({
            field, readOnly: field.readOnly, disabled: field.disabled
        }));
        fields.forEach(({field}) => {
            if (field.tagName === 'SELECT') field.disabled = true;
            else field.readOnly = true;
        });
        savingNotes.set(detail.xhr, fields);
        const status = notes.querySelector('.note-dirty-status');
        if (status) status.textContent = 'Saving personal notes. Editing will be available when this request finishes.';
    }

    function unlockNotes(detail) {
        const fields = savingNotes.get(detail.xhr);
        if (!fields) return;
        fields.forEach(({field, readOnly, disabled}) => {
            field.readOnly = readOnly;
            field.disabled = disabled;
        });
        savingNotes.delete(detail.xhr);
    }

    function recordSavedResult(target) {
        if (!target || !target.querySelectorAll) return;
        const missing = [];
        if (target.matches && target.matches('[data-forget-result-id]')) missing.push(target);
        missing.push(...target.querySelectorAll('[data-forget-result-id]'));
        missing.forEach(marker => {
            if (marker.dataset.forgetResultId === returnId) {
                returnId = '';
                try { localStorage.removeItem(returnKey); } catch (_) {}
            }
        });
        const markers = [];
        if (target.matches && target.matches('[data-saved-result-id]')) markers.push(target);
        markers.push(...target.querySelectorAll('[data-saved-result-id]'));
        if (markers.length && validId(markers[0].dataset.savedResultId)) {
            returnId = markers[0].dataset.savedResultId;
            try { localStorage.setItem(returnKey, returnId); } catch (_) {}
            scheduleResumeRefresh();
        }
    }

    function requestStatus(message) {
        const status = document.getElementById('request-status');
        if (status) status.textContent = message;
    }

    function elapsedText() {
        const seconds = Math.max(0, Math.floor((Date.now() - startedAt) / 1000));
        return `Elapsed: ${seconds} second${seconds === 1 ? '' : 's'}.`;
    }

    function lockGenerationButtons() {
        disabledButtons = Array.from(document.querySelectorAll(
            '#advisorForm button[type="submit"], #advisorForm button[hx-post="/roundtable"], #response form[hx-post="/roundtable/retry"] button[type="submit"]'
        ), button => ({button, disabled: button.disabled, wasWaiting: Boolean(button.dataset.waiting)}));
        disabledButtons.forEach(({button}) => {
            button.disabled = true;
            button.dataset.requestPending = 'true';
        });
    }

    function finishRequest(detail, failed) {
        if (!activeRequest || detail.xhr !== activeRequest) return;
        clearInterval(elapsedTimer);
        activeRequest = null;
        const response = document.getElementById('response');
        if (response) response.setAttribute('aria-busy', 'false');
        disabledButtons.forEach(({button, disabled, wasWaiting}) => {
            delete button.dataset.requestPending;
            // A retry countdown may still require the button to stay disabled.
            button.disabled = (disabled && !wasWaiting) || Boolean(button.dataset.waiting);
        });
        disabledButtons = [];
        requestStatus(failed
            ? `Request could not finish. Your question remains in the form. Review the error or try again. ${elapsedText()}`
            : `Request finished. Review the result and any recovery message below. ${elapsedText()}`);
    }

    document.body.addEventListener('htmx:configRequest', event => {
        if (event.detail.target && event.detail.target.id === 'resumePanel' && returnId) {
            event.detail.parameters.result_id = returnId;
        }
    });

    document.body.addEventListener('htmx:beforeRequest', event => {
        const detail = event.detail;
        if (!detail.target || detail.target.id !== 'response') return;
        const requestPath = detail.requestConfig && detail.requestConfig.path || '';
        if (requestPath.startsWith('/runs/') && !requestPath.endsWith('/resume') && !requestPath.endsWith('/pause')) return;
        if (activeRequest) {
            event.preventDefault();
            return;
        }
        activeRequest = detail.xhr;
        startedAt = Date.now();
        const path = detail.requestConfig && detail.requestConfig.path || '';
        waitingText = path.startsWith('/result/')
            ? 'Opening saved work.'
            : 'Waiting for the advisors. Responses appear when this request returns.';
        detail.target.setAttribute('aria-busy', 'true');
        // HTMX has already collected form values before beforeRequest fires.
        lockGenerationButtons();
        requestStatus('Submitting request. Your current question stays in the form.');
        elapsedTimer = setInterval(() => { const elapsed = document.getElementById('request-elapsed'); if (elapsed) elapsed.textContent = elapsedText(); }, 1000);
    });

    document.body.addEventListener('htmx:beforeSend', event => {
        if (event.detail.xhr === activeRequest) requestStatus(`${waitingText} ${elapsedText()}`);
        // Values are already serialized. Lock only while this note snapshot is saving.
        lockNotes(event.detail);
    });

    document.body.addEventListener('htmx:afterRequest', event => {
        finishRequest(event.detail, event.detail.failed === true || event.detail.successful === false);
        unlockNotes(event.detail);
    });

    ['htmx:sendError', 'htmx:timeout', 'htmx:sendAbort'].forEach(name => {
        document.body.addEventListener(name, event => {
            finishRequest(event.detail, true);
            unlockNotes(event.detail);
            const notes = event.detail.elt && event.detail.elt.closest('.personal-notes');
            const status = notes && notes.querySelector('.note-dirty-status');
            if (status) status.textContent = 'Could not save. Your entered notes remain here. Try Save personal notes again.';
        });
    });

    document.body.addEventListener('htmx:beforeSwap', event => {
        const target = event.detail.target;
        const xhr = event.detail.xhr;
        if (xhr && xhr.status >= 400 && xhr.responseText.includes('data-operation-error') && target && ['operation-status', 'save-status', 'roundtable-retry-status'].includes(target.id)) {
            event.detail.shouldSwap = true;
            event.detail.isError = true;
        }
        if (target && target.matches('.personal-notes') &&
            [400, 403, 404, 503].includes(xhr.status) &&
            xhr.responseText.includes('personal-notes')) {
            // Only the notes endpoint's own preserved-value fragment opts in.
            event.detail.shouldSwap = true;
            event.detail.isError = false;
        }
        if (target && target.id === 'response' && xhr.status === 404 &&
            xhr.responseText.includes('data-forget-result-id')) {
            event.detail.shouldSwap = true;
        }
    });

    document.body.addEventListener('htmx:afterSwap', event => {
        // outerHTML swaps replace detail.target; the event bubbles from the new node.
        const target = event.target && event.target !== document.body ? event.target : event.detail.target;
        recordSavedResult(target);
    });
    document.body.addEventListener('resultSaved', scheduleResumeRefresh);

    document.body.addEventListener('input', event => {
        const notes = event.target.closest('.personal-notes');
        if (!notes) return;
        const status = notes.querySelector('.note-dirty-status');
        if (status) status.textContent = 'Unsaved personal notes. Choose Save personal notes to keep this stopping point.';
        const savedStatus = notes.querySelector('.save-status');
        if (savedStatus) savedStatus.remove();
    });

    document.body.addEventListener('click', async event => {
        const button = event.target.closest('button[data-copy-target]');
        if (!button) return;
        const field = document.getElementById(button.dataset.copyTarget);
        const block = button.closest('.copy-block, .personal-notes');
        const status = block && block.querySelector('.copy-status');
        if (!field || !status) return;
        const value = field.value === undefined ? field.textContent : field.value;
        if (!value.trim()) {
            status.textContent = 'Nothing to copy yet.';
            field.focus();
            return;
        }
        try {
            await navigator.clipboard.writeText(value);
            status.textContent = 'Copied.';
        } catch (_) {
            field.focus();
            if (field.select) field.select();
            status.textContent = 'Clipboard access was unavailable. The text is selected and remains available to copy.';
        }
    });

    const clearSearch = document.getElementById('clear-history-search');
    if (clearSearch) clearSearch.addEventListener('click', () => {
        const query = document.getElementById('history-query');
        const form = document.getElementById('historySearch');
        if (form && form.reset) form.reset();
        if (query) {
            query.value = '';
            query.focus();
        }
        if (form) form.requestSubmit();
    });
})();
