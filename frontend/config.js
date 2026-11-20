// A interface servida pela API usa a mesma origem. GitHub Pages usa o servidor publicado.
window.ASHLEY_API_URL = window.ASHLEY_API_URL ??
  (location.hostname.endsWith('.github.io') ? 'https://ashley-1-demo.onrender.com' : '');
