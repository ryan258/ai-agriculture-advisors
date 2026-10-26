const test = require('node:test');
const assert = require('node:assert/strict');
const {storage, reconciled} = require('../static/js/note-drafts.js');

test('a lost storage write keeps the newest dictation in memory over a stale durable draft', () => {
    const stale = {values: {next_step: 'old'}};
    const drafts = storage({getItem: () => JSON.stringify(stale), setItem() {throw Error('quota');}});
    const latest = {values: {next_step: 'new dictated continuation'}};
    assert.equal(drafts.write('one', latest), false);
    assert.deepEqual(drafts.read('one'), latest);
});

test('only a confirmed save of the matching snapshot clears a draft', () => {
    const values = {title: 'Fictional', next_step: 'Keep the qualification'};
    assert.equal(reconciled({values}, values, true), 'clear');
    assert.equal(reconciled({values}, values, false), 'restore');
    assert.equal(reconciled({values}, null, true), 'restore');
});

test('dictation arriving after the submitted snapshot survives a successful older save', () => {
    const sent = {next_step: 'First draft'};
    const latest = {values: {next_step: 'First draft plus newer dictated context'}};
    assert.equal(reconciled(latest, sent, true), 'restore');
});

test('switching results retains separate drafts and deliberate discard clears only its key', () => {
    const values = new Map();
    const drafts = storage({getItem: key => values.get(key) || null, setItem: (key, value) => values.set(key, value), removeItem: key => values.delete(key)});
    drafts.write('first', {values: {outcome: 'First'}});
    drafts.write('second', {values: {outcome: 'Second'}});
    drafts.remove('first');
    assert.equal(drafts.read('first'), null);
    assert.equal(drafts.read('second').values.outcome, 'Second');
});
