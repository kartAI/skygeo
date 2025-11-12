// Enable file bar
const bar = document.getElementById('fileBar');
const fs = document.getElementById('fileSize');
const barWidth = bar.clientWidth;

let cl = null;
const fileHead = fetch(
  "http://localhost:8081/parquet/n50_samferdsel_senterlinje.snappy.parquet",
  // "http://localhost:8081/fgb/hurtigurten.fgb",
  {method: 'HEAD'}
).then(fh => {
  cl = fh.headers.get('content-length');
  fs.textContent = `${Number(cl / 1024 / 1024, 2).toFixed(2)} MB`
})

// Register the Service Worker
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('sw.js').then(() => {
    console.log('[main] Service Worker registered.');
  });

  // Listen for messages from the SW
  navigator.serviceWorker.addEventListener('message', event => {
    const data = event.data;
    if (data?.type === 'range-log') {
      if (data.start && data.end) {
          const left = Math.ceil((data.start / cl) * barWidth);
          const width = Math.ceil(((data.end - data.start) / cl) * barWidth);

          const rangeDiv = document.createElement('div');
          rangeDiv.className = 'range';
          rangeDiv.style.left = `${left}px`;
          rangeDiv.style.width = `${width}px`;

          // Calculate size in KB
          const sizeKB = ((data.end - data.start) / 1024).toFixed(2);

          // Create tooltip element
          const tooltip = document.createElement('div');
          tooltip.className = 'tooltip';
          tooltip.innerText = `Bytes: ${data.start}-${data.end} | Size: ${sizeKB} KB`;
          tooltip.style.position = 'absolute';
          tooltip.style.padding = '5px 8px';
          tooltip.style.background = 'rgba(0,0,0,0.7)';
          tooltip.style.color = '#fff';
          tooltip.style.borderRadius = '4px';
          tooltip.style.fontSize = '18px';
          tooltip.style.pointerEvents = 'none';
          tooltip.style.opacity = '0';
          tooltip.style.transition = 'opacity 0.2s';
          tooltip.style.zIndex = 10000;

          // Show tooltip on hover
          rangeDiv.addEventListener('mouseenter', (e) => {
              tooltip.style.opacity = '1';
              document.body.appendChild(tooltip);
          });

          rangeDiv.addEventListener('mousemove', (e) => {
              tooltip.style.left = e.pageX + 10 + 'px';
              tooltip.style.top = e.pageY + 10 + 'px';
          });

          rangeDiv.addEventListener('mouseleave', () => {
              tooltip.style.opacity = '0';
              tooltip.remove();
          });

          bar.appendChild(rangeDiv);
      }
    }
  });
}

const getDb = async () => {
  const duckdb = window.duckdbduckdbWasm;
  // @ts-ignore
  if (window._db) return window._db;
  const JSDELIVR_BUNDLES = duckdb.getJsDelivrBundles();

  // Select a bundle based on browser checks
  const bundle = await duckdb.selectBundle(JSDELIVR_BUNDLES);

  const worker_url = URL.createObjectURL(
    new Blob([`importScripts("${bundle.mainWorker}");`], {
      type: "text/javascript",
    })
  );

  // Instantiate the asynchronous version of DuckDB-wasm
  const worker = new Worker(worker_url);
  // const logger = null //new duckdb.ConsoleLogger();
  const logger = new duckdb.ConsoleLogger();
  const db = new duckdb.AsyncDuckDB(logger, worker);
  await db.instantiate(bundle.mainModule, bundle.pthreadWorker);
  URL.revokeObjectURL(worker_url);
  window._db = db;
  return db;
};

import * as duckdbduckdbWasm from "https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@1.28.1-dev106.0/+esm";
window.duckdbduckdbWasm = duckdbduckdbWasm;

let conn;

async function initDB() {
  const db = await getDb();
  conn = await db.connect();
  await conn.query("INSTALL spatial;");
  await conn.query("LOAD spatial;");
  await conn.query("CREATE VIEW samferdsel_senterlinje AS select * from read_parquet('http://localhost:8081/parquet/n50_samferdsel_senterlinje.snappy.parquet');")
  console.log("DB Ready!");
  enableQueryButton();
}

const enableQueryButton = () => {
  const btn = document.getElementById('queryButton');
  btn.textContent = 'Run';
  btn.disabled = false;
}

window.runQuery = async function () {
  // const bar = document.getElementById('fileBar');
  // bar.innerHTML = '';
  const sql = document.getElementById("sqlInput").value.trim();
  const outputDiv = document.getElementById("output");
  
  if (!sql) {
    outputDiv.innerHTML = "<p style='color:red;'>Please enter a SQL query</p>";
    return;
  }

  try {
    const result = await conn.query(sql);
    const data = result.toArray();
    outputDiv.innerHTML = `${JSON.stringify(data, null, 2)}`;
  } catch (err) {
    outputDiv.innerHTML = `${err.message}`;
  }
};

initDB();
