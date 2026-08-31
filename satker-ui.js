/* Temporary compatibility bridge for the dashboard redesign. */
(() => {
  const loadCss = () => {
    if (document.querySelector('link[data-jagat-modern-css]')) return;
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = 'dashboard-modern.css?v=6.7.0';
    link.dataset.jagatModernCss = '1';
    document.head.appendChild(link);
  };
  const loadJs = () => {
    if (document.querySelector('script[data-jagat-modern-js]')) return;
    const script = document.createElement('script');
    script.src = 'dashboard-modern.js?v=6.7.0';
    script.dataset.jagatModernJs = '1';
    document.head.appendChild(script);
  };
  loadCss();
  loadJs();
})();
