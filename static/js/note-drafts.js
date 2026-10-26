// Pure recovery decisions shared by the UI and offline regression fixtures.
(() => {
    function storage(browserStorage) {
        const memory = new Map();
        return {
            read(key) {
                if (memory.has(key)) return memory.get(key);
                try { return JSON.parse(browserStorage.getItem(key)); } catch (_) { return null; }
            },
            write(key, value) {
                memory.set(key, value);
                try { browserStorage.setItem(key, JSON.stringify(value)); return true; } catch (_) { return false; }
            },
            remove(key) {
                memory.set(key, null);
                try { browserStorage.removeItem(key); return true; } catch (_) { return false; }
            }
        };
    }
    function reconciled(draft, submitted, saved) {
        if (saved && submitted && draft && JSON.stringify(draft.values) === JSON.stringify(submitted)) return 'clear';
        return draft && draft.values && typeof draft.values === 'object' ? 'restore' : 'none';
    }
    const api = {storage, reconciled};
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    else globalThis.AdvisorNoteDrafts = api;
})();
