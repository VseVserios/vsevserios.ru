(function () {
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  document.body.addEventListener('htmx:configRequest', function (event) {
    const token = getCookie('csrftoken');
    if (token) {
      event.detail.headers['X-CSRFToken'] = token;
    }
  });

  function findConfirmMessage(form, submitter) {
    if (submitter && submitter.getAttribute) {
      const btnMsg = submitter.getAttribute('data-confirm');
      if (btnMsg) return btnMsg;
    }
    if (form && form.getAttribute) {
      const formMsg = form.getAttribute('data-confirm');
      if (formMsg) return formMsg;
    }
    return null;
  }

  function setLoading(form, submitter) {
    if (!form) return;

    const buttons = Array.from(form.querySelectorAll('button[type="submit"], input[type="submit"]'));
    buttons.forEach(function (el) {
      el.disabled = true;
      if (el.classList) el.classList.add('opacity-60');
    });

    const btn = submitter && submitter.tagName ? submitter : buttons[0];
    if (!btn) return;
    const loadingText = (btn.getAttribute && btn.getAttribute('data-loading-text')) || form.getAttribute('data-loading-text');
    if (!loadingText) return;

    if (btn.tagName.toLowerCase() === 'button') {
      if (!btn.dataset.originalText) {
        btn.dataset.originalText = btn.textContent || '';
      }
      btn.textContent = loadingText;
    } else {
      if (!btn.dataset.originalValue) {
        btn.dataset.originalValue = btn.value || '';
      }
      btn.value = loadingText;
    }
  }

  document.addEventListener('submit', function (e) {
    const form = e.target;
    if (!form || !(form instanceof HTMLFormElement)) return;

    const submitter = e.submitter;
    const msg = findConfirmMessage(form, submitter);
    if (msg && !window.confirm(msg)) {
      e.preventDefault();
      return;
    }

    setLoading(form, submitter);
  }, true);

  function applyProgressBars(root) {
    const scope = root || document;
    scope.querySelectorAll('[data-progress]').forEach(function (el) {
      const raw = el.getAttribute('data-progress');
      const n = parseInt(raw || '0', 10);
      const percent = Number.isFinite(n) ? Math.max(0, Math.min(100, n)) : 0;
      const bar = el.querySelector('[data-progress-bar]');
      if (!bar) return;
      bar.style.width = percent + '%';
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      applyProgressBars(document);
    });
  } else {
    applyProgressBars(document);
  }

  document.body.addEventListener('htmx:afterSwap', function (event) {
    applyProgressBars(event.target);
  });

  function initReveal(root) {
    const scope = root || document;
    const nodes = Array.from(scope.querySelectorAll('[data-reveal]'));
    if (!nodes.length) return;

    if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      nodes.forEach(function (el) {
        el.classList.remove('reveal-init');
        el.classList.add('reveal-show');
      });
      return;
    }

    nodes.forEach(function (el) {
      if (el.classList.contains('reveal-show')) return;
      el.classList.add('reveal-init');
    });

    if (!('IntersectionObserver' in window)) {
      nodes.forEach(function (el) {
        el.classList.add('reveal-show');
      });
      return;
    }

    const obs = new IntersectionObserver(function (entries, observer) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        const el = entry.target;
        el.classList.add('reveal-show');
        observer.unobserve(el);
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -10% 0px' });

    nodes.forEach(function (el) {
      if (el.classList.contains('reveal-show')) return;
      obs.observe(el);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      initReveal(document);
    });
  } else {
    initReveal(document);
  }

  document.body.addEventListener('htmx:afterSwap', function (event) {
    initReveal(event.target);
  });

  function findSwipeForm(value) {
    return document.querySelector('form[data-swipe="' + value + '"]');
  }

  function submitSwipe(value) {
    const form = findSwipeForm(value);
    if (!form) return;
    if (typeof form.requestSubmit === 'function') {
      form.requestSubmit();
      return;
    }
    form.submit();
  }

  function submitUndo() {
    const form = document.querySelector('form[action$="/swipe/undo/"]');
    if (!form) return;
    if (typeof form.requestSubmit === 'function') {
      form.requestSubmit();
      return;
    }
    form.submit();
  }

  document.addEventListener('keydown', function (e) {
    const tag = (e.target && e.target.tagName) ? e.target.tagName.toLowerCase() : '';
    if (tag === 'input' || tag === 'textarea' || tag === 'select') return;

    if (e.key === 'ArrowLeft' || e.key === 'a' || e.key === 'A') {
      e.preventDefault();
      submitSwipe('pass');
    } else if (e.key === 'ArrowRight' || e.key === 'd' || e.key === 'D') {
      e.preventDefault();
      submitSwipe('like');
    } else if (e.key === 'Backspace') {
      e.preventDefault();
      submitUndo();
    }
  });

  function setSwipeDisabled(disabled) {
    document.querySelectorAll('form[data-swipe] button[type="submit"]').forEach(function (btn) {
      btn.disabled = disabled;
      if (disabled) {
        btn.classList.add('opacity-60');
      } else {
        btn.classList.remove('opacity-60');
      }
    });
  }

  function isSwipeRequestTarget(el) {
    if (!el) return false;
    const form = el.closest ? el.closest('form') : null;
    if (!form) return false;
    if (form.matches && form.matches('form[data-swipe]')) return true;
    const action = form.getAttribute ? (form.getAttribute('action') || '') : '';
    return action.endsWith('/swipe/undo/');
  }

  function setSwipeIndicatorVisible(visible) {
    const card = document.getElementById('card');
    if (!card) return;
    const indicator = card.querySelector('#swipe-indicator');
    if (!indicator) return;
    if (visible) {
      indicator.classList.remove('hidden');
    } else {
      indicator.classList.add('hidden');
    }
  }

  document.body.addEventListener('htmx:beforeRequest', function (event) {
    if (!isSwipeRequestTarget(event.target)) return;
    setSwipeDisabled(true);
    setSwipeIndicatorVisible(true);
  });

  document.body.addEventListener('htmx:afterRequest', function (event) {
    if (!isSwipeRequestTarget(event.target)) return;
    setSwipeDisabled(false);
    setSwipeIndicatorVisible(false);
  });
})();
