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
}

window.runQuery = async function () {
  const sql = document.getElementById("sqlInput").value.trim();
  const outputDiv = document.getElementById("output");
  
  if (!sql) {
    outputDiv.innerHTML = "<p style='color:red;'>Please enter a SQL query</p>";
    return;
  }

  try {
    const result = await conn.query(sql);
    const data = result.toArray();
    outputDiv.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
  } catch (err) {
    outputDiv.innerHTML = `<pre style="color:red;">${err.message}</pre>`;
  }
};

initDB();
