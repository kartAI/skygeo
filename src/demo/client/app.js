document.addEventListener('DOMContentLoaded', () => {
  // Inject nav
  fetch('nav.html')
    .then(res => res.text())
    .then(html => {
      const header = document.getElementById('navbar');
      header.innerHTML = html;

      // Highlight active link
      const links = header.querySelectorAll('a');
      links.forEach(link => {
        if(link.getAttribute('href') === window.location.pathname.split('/').pop()){
          link.setAttribute('aria-current','page');
        }
      });
    });

  // Inject footer
  const footer = document.getElementById('footer');
  if (footer) {
    footer.innerHTML = `
      <p>© 2025 My Site</p>
    `;
  }
});

