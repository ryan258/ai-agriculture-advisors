const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

test('retry countdown updates visual seconds and announces only waiting/ready milestones', () => {
    const button = {dataset: {retryAt: '3'}, disabled: false};
    const status = {textContent: ''}, countdown = {textContent: ''};
    let now = 0, tick;
    const document = {
        querySelectorAll: () => [button],
        getElementById: id => id === 'roundtable-retry-status' ? status : countdown,
        body: {addEventListener() {}}
    };
    const source = fs.readFileSync(path.join(__dirname, '../static/js/roundtable.js'), 'utf8');
    vm.runInNewContext(source, {document, Date: {now: () => now}, setInterval: fn => {tick = fn; return 1;}, clearInterval() {}});
    const waiting = status.textContent;
    assert.match(waiting, /minimum wait/);
    assert.equal(button.disabled, true);
    now = 1000; tick();
    assert.equal(status.textContent, waiting);
    assert.match(countdown.textContent, /2 seconds/);
    now = 4000; tick();
    assert.equal(button.disabled, false);
    assert.match(status.textContent, /Ready to retry/);
    assert.equal(countdown.textContent, '');
});
