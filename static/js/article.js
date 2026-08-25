const translationCache = new Map();
let currentLang = 'de';

async function translateWord(word) {
    const cleanWord = word.toLowerCase().replace(/[.,!?;:()\[\]{}"'\u201c\u201d]/g, '');
    
    if (translationCache.has(cleanWord)) {
        return translationCache.get(cleanWord);
    }
    
    try {
        const response = await fetch(`https://api.mymemory.translated.net/get?q=${encodeURIComponent(cleanWord)}&langpair=de|tr`);
        const data = await response.json();
        const translation = data.responseData?.translatedText || 'Çeviri bulunamadı';
        translationCache.set(cleanWord, translation);
        return translation;
    } catch (e) {
        console.error('Translation error:', e);
        return 'Çeviri yapılamadı';
    }
}

function showLevel(level) {
    document.querySelectorAll('.version-panel').forEach(panel => {
        panel.classList.toggle('active', panel.dataset.level === level);
    });
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.level === level);
    });
    
    const activePanel = document.querySelector(`.version-panel[data-level="${level}"]`);
    if (activePanel) {
        currentLang = activePanel.querySelector('.version-content').dataset.lang || 'de';
        setupWordClick(activePanel);
    }
}

function setupWordClick(panel) {
    const content = panel.querySelector('.version-content');
    if (!content || content.dataset.processed) return;
    
    content.dataset.processed = 'true';
    
    content.addEventListener('click', async (e) => {
        const target = e.target;
        if (target.classList.contains('word-tooltip')) return;
        
        const textNode = findTextNode(target);
        if (!textNode) return;
        
        const range = document.createRange();
        range.selectNodeContents(textNode);
        const selection = window.getSelection();
        
        if (selection.rangeCount > 0) {
            const selRange = selection.getRangeAt(0);
            const word = selRange.toString().trim();
            
            if (word && word.length > 1 && /^[a-zA-ZäöüßÄÖÜ]+$/.test(word)) {
                const translation = await translateWord(word);
                showTooltip(selRange, word, translation);
            }
        }
    });
    
    content.addEventListener('dblclick', (e) => {
        const textNode = findTextNode(e.target);
        if (!textNode) return;
        
        const range = document.createRange();
        range.selectNodeContents(textNode);
        const selection = window.getSelection();
        
        if (selection.rangeCount > 0) {
            const selRange = selection.getRangeAt(0);
            const word = selRange.toString().trim();
            
            if (word && word.length > 1 && /^[a-zA-ZäöüßÄÖÜ]+$/.test(word)) {
                translateWord(word).then(translation => {
                    showTooltip(selRange, word, translation);
                });
            }
        }
    });
}

function findTextNode(element) {
    if (element.nodeType === Node.TEXT_NODE) return element;
    if (element.classList.contains('version-content')) {
        const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT);
        let node;
        while (node = walker.nextNode()) {
            if (node.textContent.trim()) return node;
        }
    }
    return element.firstChild?.nodeType === Node.TEXT_NODE ? element.firstChild : null;
}

function showTooltip(range, word, translation) {
    removeExistingTooltips();
    
    const span = document.createElement('span');
    span.className = 'word-tooltip';
    span.dataset.tr = `${word} → ${translation}`;
    span.textContent = word;
    
    range.deleteContents();
    range.insertNode(span);
    range.collapseAfter(span);
    
    document.addEventListener('click', removeExistingTooltips, { once: true });
}

function removeExistingTooltips() {
    document.querySelectorAll('.word-tooltip').forEach(tooltip => {
        const parent = tooltip.parentNode;
        parent.replaceChild(document.createTextNode(tooltip.textContent), tooltip);
        parent.normalize();
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const firstTab = document.querySelector('.tab-btn');
    if (firstTab) {
        firstTab.classList.add('active');
        const firstLevel = firstTab.dataset.level;
        document.querySelector(`.version-panel[data-level="${firstLevel}"]`)?.classList.add('active');
        setupWordClick(document.querySelector(`.version-panel[data-level="${firstLevel}"]`));
    }
});