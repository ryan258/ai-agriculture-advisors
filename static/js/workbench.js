// Local drafts, explicit input selection, and milestone status. No provider calls here.
(() => {
    const form = document.getElementById('advisorForm');
    if (!form) return;
    const cardHost = document.getElementById('source-cards');
    const draftKey = 'ai-advisors-task-draft-v3';
    const notePrefix = 'ai-advisors-note-draft-';
    const submittedNotes = new Map();
    const savedNoteBaselines = new Map();
    let lastMilestone = '';
    let sourceSequence = 0;

    let browserStorage;
    try { browserStorage = window.localStorage; } catch (_) { browserStorage = null; }
    const {read, write, remove} = AdvisorNoteDrafts.storage(browserStorage);
    const message = text => { const el = document.getElementById('operation-status'); if (el) el.textContent = text; };
    const freshKey = () => { document.getElementById('submission-key').value = window.crypto && crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(16).slice(2)}`; };

    function taskValues() {
        const brief = {};
        form.querySelectorAll('[data-task-field]').forEach(field => { if (field.value) brief[field.dataset.taskField] = field.value; });
        const sources = Array.from(cardHost.querySelectorAll('.source-card'), card => {
            const result = {};
            card.querySelectorAll('[data-source-field]').forEach(field => { result[field.dataset.sourceField] = field.value; });
            return result;
        }).filter(item => item.passage || item.label || item.reference);
        return {brief, sources};
    }

    function rememberTask() { write(draftKey, taskValues()); freshKey(); updatePlan(); }

    function addSource(value = {}) {
        if (cardHost.querySelectorAll('.source-card').length >= 8) { message('Use at most eight source excerpts.'); return; }
        const card = document.createElement('fieldset');
        card.className = 'source-card';
        const legend = document.createElement('legend'); legend.textContent = 'Supplied source excerpt'; card.append(legend);
        const sequence = ++sourceSequence;
        [['label', 'Source label', 'input'], ['date', 'Source date (if known)', 'input'], ['reference', 'Reference, not opened contents', 'input'], ['passage', 'Supplied passage', 'textarea']].forEach(([key, caption, tag]) => {
            const label = document.createElement('label'); label.htmlFor = `source-${sequence}-${key}`; label.textContent = caption;
            const field = document.createElement(tag); field.id = label.htmlFor; field.dataset.sourceField = key; field.maxLength = key === 'passage' ? 12000 : key === 'reference' ? 2000 : key === 'date' ? 100 : 200;
            if (tag === 'textarea') field.rows = 5;
            field.value = value[key] || ''; card.append(label, field);
        });
        const button = document.createElement('button'); button.type = 'button'; button.className = 'outline'; button.textContent = 'Remove this source';
        button.addEventListener('click', () => { card.remove(); rememberTask(); }); card.append(button); cardHost.append(card);
    }

    function updatePlan() {
        const count = form.querySelectorAll('input[name="roles"]:checked').length;
        const rounds = Number(document.getElementById('rounds').value);
        document.getElementById('run-plan').textContent = `Individual answers: ${count} calls. Roundtable: ${count * rounds + 1} calls before bounded synthesis fallback. Supplied source cards: ${cardHost.querySelectorAll('.source-card').length}.`;
    }

    function noteValues(notes) {
        const values = {};
        notes.querySelectorAll('input[name]:not([type="hidden"]), textarea[name], select[name]').forEach(field => { values[field.name] = field.value; });
        return values;
    }

    function restoreNotes() {
        document.querySelectorAll('.personal-notes[data-result-id]').forEach(notes => {
            if (notes.dataset.initialized) return;
            notes.dataset.initialized = 'true';
            if (notes.dataset.error !== 'true') savedNoteBaselines.set(notes.dataset.resultId, noteValues(notes));
            notes._savedValues = savedNoteBaselines.get(notes.dataset.resultId) || noteValues(notes);
            const key = notePrefix + notes.dataset.resultId;
            const saved = submittedNotes.get(notes.dataset.resultId);
            const draft = read(key);
            const recovery = AdvisorNoteDrafts.reconciled(draft, saved, notes.dataset.saved === 'true');
            if (recovery === 'clear') {
                remove(key); notes.dataset.dirty = 'false';
            } else if (recovery === 'restore') {
                notes.querySelectorAll('[name]').forEach(field => { if (typeof draft.values[field.name] === 'string') field.value = draft.values[field.name]; });
                notes.dataset.dirty = 'true';
                notes.dataset.durableDraft = draft.durable === false ? 'false' : 'true';
                const status = notes.querySelector('.note-dirty-status');
                if (status) status.textContent = 'Recovered a local note draft. It is not saved personal notes until you choose Save personal notes.';
            }
            if (notes.dataset.saved === 'true') {
                const submit = notes.querySelector('button[type="submit"]'); if (submit) submit.focus();
            }
        });
    }

    function synchronizeRun() {
        const frame = document.querySelector('#response .run-frame');
        const running = frame && ['queued', 'running'].includes(frame.dataset.runState);
        document.querySelectorAll('#advisorForm button[type="submit"], #advisorForm button[hx-post="/roundtable"]').forEach(button => {
            if (running) { button.dataset.runLocked = 'true'; button.disabled = true; }
            else if (button.dataset.runLocked) { delete button.dataset.runLocked; button.disabled = Boolean(button.dataset.waiting || button.dataset.requestPending); }
        });
        const response = document.getElementById('response');
        response.setAttribute('aria-live', running ? 'off' : 'polite');
        if (frame) {
            const milestone = `${frame.dataset.runId}:${frame.dataset.runState}:${frame.dataset.completed || 0}`;
            if (milestone !== lastMilestone) {
                lastMilestone = milestone;
                document.getElementById('request-status').textContent = `Working run ${frame.dataset.runState}. ${frame.dataset.completed || 0} completed contributions checkpointed locally.`;
            }
        }
    }

    document.getElementById('add-source').addEventListener('click', () => { addSource(); rememberTask(); });
    document.getElementById('clear-task-context').addEventListener('click', () => {
        form.querySelectorAll('[data-task-field]').forEach(field => { field.value = ''; });
        cardHost.replaceChildren(); remove(draftKey); freshKey(); updatePlan();
        message('Optional task context and supplied excerpts cleared for the next submission. Saved runs retain their captured input.');
    });
    document.getElementById('new-attempt').addEventListener('click', () => { freshKey(); message('The next submission will start a new run with the visible input.'); });
    form.addEventListener('input', rememberTask);
    form.addEventListener('change', rememberTask);
    document.body.addEventListener('htmx:configRequest', event => {
        const detail = event.detail;
        if (['/query', '/roundtable'].includes(detail.path)) {
            const values = taskValues();
            detail.parameters.task_brief = JSON.stringify(values.brief);
            detail.parameters.sources = JSON.stringify(values.sources);
        }
        const assetForm = detail.elt && detail.elt.closest('[data-save-starter]');
        if (assetForm) {
            detail.parameters.panel_id = document.getElementById('panel').value;
            detail.parameters.roles = Array.from(form.querySelectorAll('input[name="roles"]:checked'), field => field.value);
        }
    });
    document.body.addEventListener('htmx:beforeRequest', event => {
        const notes = document.querySelector('.personal-notes[data-dirty="true"]');
        if (notes && notes.dataset.durableDraft === 'false' && event.detail.target && event.detail.target.id === 'response') {
            event.preventDefault(); message('Browser draft storage is unavailable. Save or copy your personal notes before opening another result.');
        }
    });
    document.body.addEventListener('htmx:beforeSend', event => {
        const notes = event.detail.elt && event.detail.elt.closest('.personal-notes');
        if (notes) submittedNotes.set(notes.dataset.resultId, noteValues(notes));
    });
    document.body.addEventListener('input', event => {
        const notes = event.target.closest('.personal-notes[data-result-id]');
        if (!notes) return;
        notes.dataset.dirty = 'true';
        const key = notePrefix + notes.dataset.resultId;
        const draft = {values: noteValues(notes), durable: true};
        const durable = write(key, draft);
        notes.dataset.durableDraft = durable ? 'true' : 'false';
        if (!durable) draft.durable = false;
    });
    document.body.addEventListener('htmx:afterSwap', () => { restoreNotes(); synchronizeRun(); });
    document.body.addEventListener('htmx:afterRequest', () => setTimeout(synchronizeRun, 0));
    document.body.addEventListener('click', event => {
        const capture = event.target.closest('[data-capture-current-starter]');
        if (capture) {
            const value = document.getElementById('query').value;
            document.getElementById('starter-content').value = value;
            const name = document.getElementById('starter-name'); if (!name.value) name.value = value.slice(0, 80);
            name.focus();
        }
        const starter = event.target.closest('[data-use-starter]');
        const qualityCase = event.target.closest('[data-use-case]');
        const context = event.target.closest('[data-use-context]');
        const excerpt = event.target.closest('[data-add-excerpt]');
        const discard = event.target.closest('[data-discard-note-draft]');
        if (qualityCase) {
            const value = JSON.parse(qualityCase.dataset.useCase), current = taskValues();
            if (document.getElementById('query').value.trim() || current.sources.length || Object.keys(current.brief).length) {
                message('Current input is retained. Use Clear draft and Clear task context before preparing a fictional case.'); return;
            }
            const panel = document.getElementById('panel'); panel.value = value.panel_id; panel.dispatchEvent(new Event('change', {bubbles: true}));
            form.querySelectorAll('input[name="roles"]').forEach(field => { field.checked = value.roles.includes(field.value); });
            const question = document.getElementById('query'); question.value = value.query; question.dispatchEvent(new Event('input', {bubbles: true}));
            value.sources.forEach(addSource); rememberTask(); question.focus();
            message('Fictional case prepared. Review the visible question and supplied passages before deliberately sending it.');
        }
        if (starter) {
            const query = document.getElementById('query');
            if (query.value.trim()) { message('Your current question is retained. Clear the draft before choosing a starter.'); return; }
            const value = JSON.parse(starter.dataset.useStarter);
            const panel = document.getElementById('panel'); panel.value = value.panel_id; panel.dispatchEvent(new Event('change', {bubbles: true}));
            form.querySelectorAll('input[name="roles"]').forEach(field => { field.checked = value.roles.includes(field.value); });
            query.value = value.query; query.dispatchEvent(new Event('input', {bubbles: true})); query.focus();
        }
        if (context) {
            const value = JSON.parse(context.dataset.useContext); const field = document.getElementById('task-background');
            if (field.value.trim()) { message('The current background is retained. Clear that field before selecting another context.'); return; }
            field.value = value.background; field.dispatchEvent(new Event('input', {bubbles: true})); field.focus();
        }
        if (excerpt) {
            const passage = document.getElementById('selected-excerpt').value;
            if (passage.length > 12000) { message('Shorten the visible excerpt to 12,000 characters before adding it.'); return; }
            addSource({label: excerpt.dataset.addExcerpt, passage}); rememberTask(); message('Added the supplied passage. Review it in task context before submitting.');
        }
        if (discard) {
            const notes = discard.closest('.personal-notes');
            const discardedDurably = remove(notePrefix + notes.dataset.resultId);
            notes.querySelectorAll('[name]').forEach(field => { if (notes._savedValues && field.name in notes._savedValues) field.value = notes._savedValues[field.name]; });
            notes.dataset.dirty = 'false'; notes.querySelector('.note-dirty-status').textContent = discardedDurably ? 'Local note draft discarded. Showing the saved values.' : 'Showing saved values for this page. Browser storage prevented removing an older draft; it may reappear after reload.';
        }
    });
    window.addEventListener('beforeunload', event => {
        if (document.querySelector('.personal-notes[data-dirty="true"][data-durable-draft="false"]')) { event.preventDefault(); event.returnValue = ''; }
    });
    document.addEventListener('keydown', event => {
        if (!event.altKey || event.ctrlKey || event.metaKey) return;
        const key = event.key.toLowerCase();
        const target = key === 'q' ? document.getElementById('query') : key === 'f' ? document.getElementById('history-query') : key === 's' ? document.querySelector('.personal-notes button[type="submit"], .save-btn') : key === 'r' ? document.querySelector('#resumePanel button[hx-get^="/result/"]') : null;
        if (!target) return;
        event.preventDefault(); target.focus(); if (['s', 'r'].includes(key) && !target.disabled) target.click();
    });
    const draft = read(draftKey);
    if (draft && draft.brief && Array.isArray(draft.sources)) {
        form.querySelectorAll('[data-task-field]').forEach(field => { if (typeof draft.brief[field.dataset.taskField] === 'string') field.value = draft.brief[field.dataset.taskField]; });
        draft.sources.slice(0, 8).forEach(addSource);
    }
    freshKey(); updatePlan(); restoreNotes(); synchronizeRun();
})();
