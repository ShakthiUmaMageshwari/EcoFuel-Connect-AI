/**
 * EcoFuel Connect AI - i18n Translation Engine
 */

function setLanguage(lang) {
    localStorage.setItem('ecofuel_lang', lang);
    applyTranslations();
}

function getLanguage() {
    return localStorage.getItem('ecofuel_lang') || 'en';
}

function applyTranslations() {
    const lang = getLanguage();
    const dict = translations[lang] || translations['en'];
    
    // 1. Update all elements with data-i18n attribute
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (dict[key]) {
            if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
                el.placeholder = dict[key];
            } else {
                el.innerText = dict[key];
            }
        }
    });

    // 2. Update language selector active state if exists
    document.querySelectorAll('.lang-btn').forEach(btn => {
        if (btn.getAttribute('data-lang') === lang) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
    
    // 3. Update HTML lang attribute
    document.documentElement.lang = lang;
}

// Initial apply
document.addEventListener('DOMContentLoaded', applyTranslations);
