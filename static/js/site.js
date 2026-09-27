const initializeSite = () => {
  const toggle = document.querySelector('[data-menu-toggle]');
  const menu = document.querySelector('[data-menu]');
  toggle?.addEventListener('click', () => {
    const expanded = toggle.getAttribute('aria-expanded') === 'true';
    toggle.setAttribute('aria-expanded', String(!expanded));
    menu?.classList.toggle('is-open', !expanded);
  });

  const revealItems = document.querySelectorAll('[data-reveal]');
  if ('IntersectionObserver' in window) {
    document.documentElement.classList.add('reveal-ready');
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 });
    revealItems.forEach((item) => observer.observe(item));
  } else {
    revealItems.forEach((item) => item.classList.add('is-visible'));
  }

  const dialog = document.querySelector('[data-lightbox-dialog]');
  if (dialog) {
    const links = [...document.querySelectorAll('[data-lightbox]')];
    const image = dialog.querySelector('img');
    const caption = dialog.querySelector('p');
    let activeIndex = 0;
    const show = (index) => {
      activeIndex = (index + links.length) % links.length;
      const link = links[activeIndex];
      image.src = link.href;
      image.alt = link.dataset.caption || '';
      caption.textContent = link.dataset.caption || '';
    };
    links.forEach((link, index) => link.addEventListener('click', (event) => {
      event.preventDefault();
      show(index);
      dialog.showModal();
    }));
    dialog.querySelector('.lightbox-close').addEventListener('click', () => dialog.close());
    dialog.querySelector('.lightbox-prev').addEventListener('click', () => show(activeIndex - 1));
    dialog.querySelector('.lightbox-next').addEventListener('click', () => show(activeIndex + 1));
    dialog.addEventListener('click', (event) => {
      if (event.target === dialog) dialog.close();
    });
  }

  const notificationSocket = document.body.dataset.notificationSocket;
  if (notificationSocket && 'WebSocket' in window) {
    const socket = new WebSocket(notificationSocket);
    socket.addEventListener('message', (event) => {
      const payload = JSON.parse(event.data);
      document.dispatchEvent(new CustomEvent('ceobef:notification', { detail: payload }));
    });
  }

  document.addEventListener('ceobef:notification', (event) => {
    const payload = event.detail;
    const count = document.querySelector('[data-notification-count]');
    if (count) {
      count.textContent = String(Number(count.textContent || 0) + 1);
      count.hidden = false;
    }
    const notice = document.createElement('a');
    notice.className = 'live-notice';
    notice.href = payload.url || '/notifications/';
    const title = document.createElement('strong');
    title.textContent = payload.title || 'Nouvelle notification';
    const body = document.createElement('span');
    body.textContent = payload.body || '';
    notice.append(title, body);
    document.querySelector('[data-live-notices]')?.append(notice);
    window.setTimeout(() => notice.remove(), 6500);
  });
};

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeSite, { once: true });
} else {
  initializeSite();
}
