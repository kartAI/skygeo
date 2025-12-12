/**
 * Common header for all SkyGeo demos
 * Inject this script into demo pages to add a consistent navigation header
 */

(function() {
  // Determine the base path for links (relative to /docs)
  const getBasePath = () => {
    const path = window.location.pathname;
    // GitHub Pages deployment uses /skygeo as base path
    const match = path.match(/\/skygeo\/(.+)/);
    if (!match) return '/skygeo/docs';
    
    const afterSkygeo = match[1];
    const depth = afterSkygeo.split('/').filter(p => p && p !== 'index.html').length;
    
    return depth === 0 ? '/skygeo/docs' : '../'.repeat(depth - 1) + '..';
  };

  const basePath = getBasePath();
  
  // Get current page info for source code link (GitHub URL)
  const getCurrentDemoPath = () => {
    const path = window.location.pathname;
    const baseGitHub = 'https://github.com/kartAI/skygeo/tree/main/src';
    
    // Map demo URLs to source code paths - order matters (check more specific paths first)
    if (path.includes('/docs/flatgeobuf/')) return `${baseGitHub}/flatgeobuf`;
    if (path.includes('/docs/parquet/')) return `${baseGitHub}/demo`;
    if (path.includes('/docs/pmtiles_bakgrunnskart/')) return `${baseGitHub}/planetiles2pmtiles`;
    
    return baseGitHub;
  };

  const sourceCodePath = getCurrentDemoPath();

  // Create header HTML
  const headerHTML = `
    <style>
      .skygeo-header {
        background: #2c3e50;
        color: #ecf0f1;
        padding: 16px 24px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        position: relative;
        z-index: 10000;
      }
      
      .skygeo-header-content {
        max-width: 1200px;
        margin: 0 auto;
      }
      
      .skygeo-header h1 {
        margin: 0 0 8px 0;
        font-size: 1.5em;
        font-weight: 600;
      }
      
      .skygeo-header p {
        margin: 0 0 12px 0;
        font-size: 0.95em;
        opacity: 0.9;
        line-height: 1.4;
      }
      
      .skygeo-header nav {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
      }
      
      .skygeo-header a {
        color: #3498db;
        text-decoration: none;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.9em;
        transition: background-color 0.2s;
        display: inline-block;
      }
      
      .skygeo-header a:hover {
        background-color: rgba(52, 152, 219, 0.1);
        text-decoration: underline;
      }
      
      @media (max-width: 600px) {
        .skygeo-header {
          padding: 12px 16px;
        }
        
        .skygeo-header h1 {
          font-size: 1.25em;
        }
        
        .skygeo-header p {
          font-size: 0.85em;
        }
        
        .skygeo-header nav {
          flex-direction: column;
          gap: 4px;
        }
        
        .skygeo-header a {
          font-size: 0.85em;
        }
      }
    </style>
    <header class="skygeo-header">
      <div class="skygeo-header-content">
        <h1>⛅ SkyGeo 🗺️</h1>
        <p>Utforskning av cloud native formater og STAC metadata for norske geografiske datasett</p>
        <nav>
          <a href="${basePath}/">📋 Alle demoer</a>
          <a href="https://github.com/kartAI/skygeo#readme">📖 README</a>
          <a href="https://github.com/kartAI/skygeo">🔗 GitHub Repository</a>
          <a href="${sourceCodePath}">💻 Kildekode for denne demoen</a>
        </nav>
      </div>
    </header>
  `;

  // Insert header at the beginning of body
  if (document.body) {
    document.body.insertAdjacentHTML('afterbegin', headerHTML);
  } else {
    document.addEventListener('DOMContentLoaded', () => {
      document.body.insertAdjacentHTML('afterbegin', headerHTML);
    });
  }
})();
