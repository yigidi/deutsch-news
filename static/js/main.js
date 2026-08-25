function filterByLevel(level) {
    const cards = document.querySelectorAll('.news-card');
    cards.forEach(card => {
        const badges = card.querySelectorAll('.level-badge');
        const hasLevel = Array.from(badges).some(b => b.textContent === level);
        card.style.display = (!level || hasLevel) ? 'block' : 'none';
    });
    updateUrlParams({ level });
}

function filterBySource(source) {
    const cards = document.querySelectorAll('.news-card');
    cards.forEach(card => {
        const cardSource = card.querySelector('.source').textContent;
        card.style.display = (!source || cardSource.includes(source)) ? 'block' : 'none';
    });
    updateUrlParams({ source });
}

function updateUrlParams(params) {
    const url = new URL(window.location);
    Object.entries(params).forEach(([key, value]) => {
        if (value) url.searchParams.set(key, value);
        else url.searchParams.delete(key);
    });
    window.history.replaceState({}, '', url);
}

function restoreFilters() {
    const params = new URLSearchParams(window.location.search);
    const level = params.get('level');
    const source = params.get('source');
    
    if (level) {
        document.getElementById('levelFilter').value = level;
        filterByLevel(level);
    }
    if (source) {
        document.getElementById('sourceFilter').value = source;
        filterBySource(source);
    }
}

document.addEventListener('DOMContentLoaded', restoreFilters);