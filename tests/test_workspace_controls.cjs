// Headless behavior coverage using Node's standard library. No browser or packages.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '../static/js/workspace.js'), 'utf8');

class Element {
    constructor(tag = 'div', props = {}) {
        this.tagName = tag.toUpperCase();
        this.children = [];
        this.dataset = {};
        this.attributes = {};
        this.listeners = new Map();
        this.value = '';
        this.textContent = '';
        this.disabled = false;
        this.readOnly = false;
        Object.assign(this, props);
    }
    append(child) { this.children.push(child); child.parentElement = this; return child; }
    matches(selector) {
        return selector.split(',').some(part => {
            const token = part.trim();
            if (token.startsWith('.')) return (this.className || '').split(' ').includes(token.slice(1));
            if (token === '[data-saved-result-id]') return 'savedResultId' in this.dataset;
            if (token === '[data-forget-result-id]') return 'forgetResultId' in this.dataset;
            if (token === 'button[data-copy-target]') return this.tagName === 'BUTTON' && 'copyTarget' in this.dataset;
            if (token === 'input:not([type="hidden"])') return this.tagName === 'INPUT' && this.type !== 'hidden';
            return this.tagName === token.toUpperCase();
        });
    }
    closest(selector) { return this.matches(selector) ? this : this.parentElement && this.parentElement.closest(selector); }
    querySelectorAll(selector) {
        return this.children.flatMap(child => [
            ...(child.matches(selector) ? [child] : []), ...child.querySelectorAll(selector)
        ]);
    }
    querySelector(selector) { return this.querySelectorAll(selector)[0] || null; }
    addEventListener(name, callback) {
        if (!this.listeners.has(name)) this.listeners.set(name, []);
        this.listeners.get(name).push(callback);
    }
    setAttribute(name, value) { this.attributes[name] = value; }
    focus() { this.focused = true; }
    select() { this.selected = true; }
    requestSubmit() { this.submitted = true; }
    remove() { this.parentElement.children = this.parentElement.children.filter(child => child !== this); }
}

function setup({storage = {}, unavailableStorage = false, copyFails = false} = {}) {
    const body = new Element('body');
    const response = body.append(new Element('section', {id: 'response'}));
    const resume = body.append(new Element('section', {id: 'resumePanel'}));
    const status = body.append(new Element('p', {id: 'request-status'}));
    const elapsed = body.append(new Element('p', {id: 'request-elapsed'}));
    const form = body.append(new Element('form', {id: 'advisorForm'}));
    const query = form.append(new Element('textarea', {id: 'query', value: 'My dictated question'}));
    const roles = form.append(new Element('input', {type: 'checkbox'}));
    const submit = form.append(new Element('button', {type: 'submit'}));
    const roundtable = form.append(new Element('button'));
    const retry = response.append(new Element('button', {disabled: true, dataset: {waiting: 'true'}}));
    const historyForm = body.append(new Element('form', {id: 'historySearch'}));
    const search = historyForm.append(new Element('input', {id: 'history-query', value: 'old phrase'}));
    const clearSearch = historyForm.append(new Element('button', {id: 'clear-history-search'}));
    const calls = [];
    const clipboard = [];
    const stored = new Map(Object.entries(storage));
    const timeouts = new Map();
    const intervals = new Map();
    let timerId = 0;
    let now = 1000;
    const document = {
        body,
        getElementById: id => [body, ...body.querySelectorAll('*')].find(el => el.id === id) || findId(body, id),
        querySelectorAll: selector => selector.startsWith('#advisorForm button') ? [submit, roundtable, retry] : body.querySelectorAll(selector)
    };
    function findId(parent, id) {
        for (const child of parent.children) {
            if (child.id === id) return child;
            const nested = findId(child, id);
            if (nested) return nested;
        }
        return null;
    }
    vm.runInNewContext(source, {
        document,
        window: {htmx: {ajax: (...args) => calls.push(args)}},
        navigator: {clipboard: {writeText: async value => { if (copyFails) throw Error('denied'); clipboard.push(value); }}},
        localStorage: {
            getItem: key => { if (unavailableStorage) throw Error('blocked'); return stored.get(key) || null; },
            setItem: (key, value) => { if (unavailableStorage) throw Error('blocked'); stored.set(key, value); },
            removeItem: key => { if (unavailableStorage) throw Error('blocked'); stored.delete(key); }
        },
        Date: {now: () => now},
        encodeURIComponent,
        setTimeout: callback => { const id = ++timerId; timeouts.set(id, callback); return id; },
        clearTimeout: id => timeouts.delete(id),
        setInterval: callback => { const id = ++timerId; intervals.set(id, callback); return id; },
        clearInterval: id => intervals.delete(id)
    });
    async function fire(name, detail = {}, target = body) {
        const event = {detail, target, prevented: false, preventDefault() { this.prevented = true; }};
        for (const callback of body.listeners.get(name) || []) await callback(event);
        return event;
    }
    return {
        body, response, resume, status, elapsed, query, roles, submit, roundtable, retry, historyForm, search, clearSearch,
        calls, clipboard, stored, fire,
        tick: seconds => { now += seconds * 1000; for (const callback of intervals.values()) callback(); },
        flush: () => { const callbacks = [...timeouts.values()]; timeouts.clear(); callbacks.forEach(callback => callback()); }
    };
}

function addNotes(env) {
    const notes = env.response.append(new Element('section', {className: 'personal-notes'}));
    const form = notes.append(new Element('form'));
    const title = form.append(new Element('input', {value: 'My title'}));
    const next = form.append(new Element('textarea', {id: 'next', value: 'Take one step'}));
    const status = form.append(new Element('select', {value: 'waiting'}));
    const dirty = form.append(new Element('p', {className: 'note-dirty-status'}));
    return {notes, form, title, next, status, dirty};
}

test('history and notes requests never mark the result busy; generation locks only buttons', async () => {
    const env = setup();
    await env.fire('htmx:beforeRequest', {target: env.resume, xhr: {}});
    assert.equal(env.response.attributes['aria-busy'], undefined);
    const xhr = {};
    await env.fire('htmx:beforeRequest', {target: env.response, xhr, requestConfig: {path: '/roundtable'}});
    assert.equal(env.response.attributes['aria-busy'], 'true');
    assert.equal(env.submit.disabled, true);
    assert.equal(env.roundtable.disabled, true);
    assert.equal(env.query.disabled, false);
    assert.equal(env.roles.disabled, false);
    assert.equal(env.query.value, 'My dictated question');
    const duplicate = await env.fire('htmx:beforeRequest', {target: env.response, xhr: {}});
    assert.equal(duplicate.prevented, true);
    await env.fire('htmx:afterRequest', {target: env.resume, xhr: {}});
    assert.equal(env.submit.disabled, true);
    env.tick(2);
    assert.match(env.elapsed.textContent, /Elapsed: 2 seconds/);
    assert.doesNotMatch(env.status.textContent, /Elapsed: 2 seconds/, "elapsed time does not repeatedly update the live region");
    await env.fire('htmx:afterRequest', {xhr, successful: true});
    assert.equal(env.submit.disabled, false);
    assert.equal(env.retry.disabled, true, 'the existing retry countdown remains locked');
    assert.equal(env.response.attributes['aria-busy'], 'false');
    assert.match(env.status.textContent, /Request finished/);
});

test('request transport failure releases buttons without clearing the dictated question', async () => {
    const env = setup();
    const xhr = {};
    await env.fire('htmx:beforeRequest', {target: env.response, xhr});
    await env.fire('htmx:timeout', {xhr});
    assert.equal(env.submit.disabled, false);
    assert.equal(env.query.value, 'My dictated question');
    assert.match(env.status.textContent, /could not finish/);
});

test('a retry countdown that expires during another request stays ready afterward', async () => {
    const env = setup();
    const xhr = {};
    await env.fire('htmx:beforeRequest', {target: env.response, xhr});
    delete env.retry.dataset.waiting;
    await env.fire('htmx:afterRequest', {xhr, successful: false});
    assert.equal(env.retry.disabled, false);
});

test('last-opened result restores only a resume lookup, with no advisor submission', async () => {
    const env = setup({storage: {'ai-advisors-last-result': 'abcdef12'}});
    const detail = {target: env.resume, parameters: {}};
    await env.fire('htmx:configRequest', detail);
    assert.equal(detail.parameters.result_id, 'abcdef12');
    assert.equal(env.calls.length, 0);
    const marker = env.response.append(new Element('div', {dataset: {savedResultId: '1234abcd'}}));
    await env.fire('resultSaved');
    await env.fire('htmx:afterSwap', {target: new Element('div')}, marker);
    env.flush();
    assert.equal(env.stored.get('ai-advisors-last-result'), '1234abcd');
    assert.equal(env.calls.length, 1, 'save and swap notifications coalesce into one refresh');
    assert.equal(env.calls[0][0], 'GET');
    assert.equal(env.calls[0][1], '/resume?result_id=1234abcd');
});

test('missing or invalid saved IDs fall back to ordinary history', async () => {
    const env = setup({storage: {'ai-advisors-last-result': 'abcdef12'}});
    const marker = env.resume.append(new Element('div', {dataset: {forgetResultId: 'abcdef12'}}));
    await env.fire('htmx:afterSwap', {target: marker});
    assert.equal(env.stored.has('ai-advisors-last-result'), false);
    const detail = {target: env.resume, parameters: {}};
    await env.fire('htmx:configRequest', detail);
    assert.equal(detail.parameters.result_id, undefined);
    const malformed = setup({storage: {'ai-advisors-last-result': '../query'}});
    assert.equal(malformed.stored.has('ai-advisors-last-result'), false);
});

test('unavailable browser storage still permits an in-session return point', async () => {
    const env = setup({unavailableStorage: true});
    const marker = env.response.append(new Element('div', {dataset: {savedResultId: '1234abcd'}}));
    await env.fire('htmx:afterSwap', {target: marker});
    env.flush();
    assert.equal(env.calls[0][1], '/resume?result_id=1234abcd');
});

test('copy succeeds without altering reusable text', async () => {
    const env = setup();
    const block = env.response.append(new Element('div', {className: 'copy-block'}));
    const field = block.append(new Element('textarea', {id: 'copy-text', value: 'Reusable\nDictated text'}));
    const button = block.append(new Element('button', {dataset: {copyTarget: 'copy-text'}}));
    const status = block.append(new Element('p', {className: 'copy-status'}));
    await env.fire('click', {}, button);
    assert.deepEqual(env.clipboard, ['Reusable\nDictated text']);
    assert.equal(status.textContent, 'Copied.');
    assert.equal(field.value, 'Reusable\nDictated text');
});

test('clipboard denial preserves and selects readable text for manual copy', async () => {
    const env = setup({copyFails: true});
    const block = env.response.append(new Element('div', {className: 'copy-block'}));
    const field = block.append(new Element('textarea', {id: 'copy-text', value: 'Next step'}));
    const button = block.append(new Element('button', {dataset: {copyTarget: 'copy-text'}}));
    const status = block.append(new Element('p', {className: 'copy-status'}));
    await env.fire('click', {}, button);
    assert.equal(field.focused, true);
    assert.equal(field.selected, true);
    assert.equal(field.value, 'Next step');
    assert.match(status.textContent, /unavailable/);
});

test('only preserved-value personal-note errors opt in to HTTP error swapping', async () => {
    const env = setup();
    const {notes} = addNotes(env);
    const detail = {target: notes, xhr: {status: 503, responseText: '<section class="personal-notes">preserved</section>'}};
    await env.fire('htmx:beforeSwap', detail);
    assert.equal(detail.shouldSwap, true);
    assert.equal(detail.isError, false);
    const unrelated = {target: env.response, xhr: {status: 503, responseText: 'failed'}};
    await env.fire('htmx:beforeSwap', unrelated);
    assert.equal(unrelated.shouldSwap, undefined);
});

test('notes lock after serialization and unlock on failure, retaining dictated text', async () => {
    const env = setup();
    const note = addNotes(env);
    const xhr = {};
    await env.fire('htmx:beforeRequest', {target: note.notes, elt: note.form, xhr});
    assert.equal(note.next.readOnly, false, 'fields remain serializable through beforeRequest');
    assert.equal(note.status.disabled, false);
    await env.fire('htmx:beforeSend', {elt: note.form, xhr});
    assert.equal(note.next.readOnly, true, 'dictation cannot change the submitted snapshot while saving');
    assert.equal(note.title.readOnly, true);
    assert.equal(note.status.disabled, true);
    assert.match(note.dirty.textContent, /Saving personal notes/);
    await env.fire('htmx:sendError', {elt: note.form, xhr});
    assert.equal(note.next.readOnly, false);
    assert.equal(note.status.disabled, false);
    assert.equal(note.next.value, 'Take one step');
    assert.match(note.dirty.textContent, /entered notes remain/);
});

test('successful notes request unlocks controls and edits announce unsaved state', async () => {
    const env = setup();
    const note = addNotes(env);
    const xhr = {};
    await env.fire('htmx:beforeSend', {elt: note.form, xhr});
    await env.fire('htmx:afterRequest', {elt: note.form, xhr, successful: true});
    assert.equal(note.next.readOnly, false);
    assert.equal(note.status.disabled, false);
    await env.fire('input', {}, note.next);
    assert.match(note.dirty.textContent, /Unsaved personal notes/);
});

test('clear search resets the visible form and requests ordinary history', () => {
    const env = setup();
    env.clearSearch.listeners.get('click')[0]();
    assert.equal(env.search.value, '');
    assert.equal(env.search.focused, true);
    assert.equal(env.historyForm.submitted, true);
});
