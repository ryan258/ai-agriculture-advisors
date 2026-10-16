// Switching panels preserves the current question and displayed results.
(() => {
    const panels = JSON.parse(document.getElementById('panel-data').textContent);
    const advisors = JSON.parse(document.getElementById('advisor-data').textContent);
    const selector = document.getElementById('panel');
    const options = document.getElementById('advisor-options');
    const suggestions = document.getElementById('suggestions');
    const storageKey = 'ai-advisors-preferences';
    let preferences = {panel: selector.value, selections: {}};
    try {
        const saved = JSON.parse(localStorage.getItem(storageKey));
        if (saved && panels.some(panel => panel.id === saved.panel) &&
            saved.selections && typeof saved.selections === 'object' && !Array.isArray(saved.selections)) {
            preferences = saved;
        }
    } catch (_) { /* Unavailable storage must not prevent asking a question. */ }

    const queryBox = document.getElementById('query');
    const draftStatus = document.getElementById('draft-status');
    const draftKey = 'ai-advisors-draft';

    function setDraftStatus(message) {
        if (draftStatus) draftStatus.textContent = message;
    }

    function saveDraft() {
        try { localStorage.setItem(draftKey, queryBox.value); } catch (_) {}
    }

    function remember() {
        preferences.panel = selector.value;
        preferences.selections[selector.value] = Array.from(
            options.querySelectorAll('input:checked'), input => input.value
        );
        try { localStorage.setItem(storageKey, JSON.stringify(preferences)); } catch (_) {}
    }

    function showPanel() {
        const panel = panels.find(item => item.id === selector.value);
        const remembered = preferences.selections[panel.id];
        const selected = Array.isArray(remembered) ? remembered : panel.default_roles;
        options.replaceChildren();
        panel.roles.forEach(role => {
            const advisor = advisors.find(item => item.role === role);
            const row = document.createElement('div');
            row.className = 'expert-checkbox';
            const input = document.createElement('input');
            input.type = 'checkbox';
            input.name = 'roles';
            input.value = role;
            input.id = `expert-${role}`;
            input.checked = selected.includes(role);
            const label = document.createElement('label');
            label.htmlFor = input.id;
            label.textContent = advisor.label;
            row.append(input, label);
            options.append(row);
        });
        document.getElementById('panel-description').textContent = panel.description;
        suggestions.replaceChildren();
        panel.suggested_queries.forEach(suggestion => {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'chip';
            button.dataset.query = suggestion.query;
            button.textContent = suggestion.label;
            button.setAttribute('aria-label', `Use example query: ${suggestion.query}`);
            suggestions.append(button);
        });
        remember();
        document.getElementById('panel-status').textContent =
            `${panel.label} panel: ${panel.roles.length} advisors available.`;
    }

    selector.value = preferences.panel;
    selector.addEventListener('change', showPanel);
    options.addEventListener('change', remember);
    suggestions.addEventListener('click', event => {
        const chip = event.target.closest('button[data-query]');
        if (!chip) return;
        if (queryBox.value.trim() !== '') {
            setDraftStatus('Kept your current draft. Clear it first to use this example.');
            queryBox.focus();
            return;
        }
        queryBox.value = chip.dataset.query;
        saveDraft();
        setDraftStatus('');
        queryBox.focus();
    });
    queryBox.addEventListener('input', saveDraft);
    let restoredDraft = '';
    try { restoredDraft = localStorage.getItem(draftKey) || ''; } catch (_) {}
    if (restoredDraft !== '' && queryBox.value.trim() === '') {
        queryBox.value = restoredDraft;
        setDraftStatus('Restored your unsent draft.');
    }
    const clearDraft = document.getElementById('clear-draft');
    if (clearDraft) clearDraft.addEventListener('click', () => {
        queryBox.value = '';
        try { localStorage.removeItem(draftKey); } catch (_) {}
        setDraftStatus('Draft cleared.');
        queryBox.focus();
    });
    showPanel();
})();
