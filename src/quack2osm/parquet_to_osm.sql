-- parquet_to_osm.sql
-- 
-- This DuckDB script converts a (Geo)Parquet file into an OSM XML file.
-- It replicates the logic from the provided 'geojsontoosm' JavaScript file.
--
-- ASSUMPTIONS:
-- 1. Input file is named 'data.parquet' and is in the same directory.
-- 2. The parquet file is a GeoParquet file, with:
--    - A 'geometry' column (WKB)
--    - A 'properties' column (MAP(VARCHAR, VARCHAR))
-- 3. Output file will be 'output.osm'.
--
-- USAGE:
-- duckdb -c ".read parquet_to_osm.sql"
--
--------------------------------------------------------------------------------

-- Step 0: Install and load necessary extensions
INSTALL spatial;
LOAD spatial;

--------------------------------------------------------------------------------
-- STEP 1: Define Sequences
-- We use negative IDs, matching the JS logic.
--------------------------------------------------------------------------------
CREATE SEQUENCE osm_node_id_seq START -1 INCREMENT -1;
CREATE SEQUENCE osm_way_id_seq START -1 INCREMENT -1;
CREATE SEQUENCE osm_relation_id_seq START -1 INCREMENT -1;

--------------------------------------------------------------------------------
-- STEP 2: Load Features
-- Read the Parquet file and create a base table of features.
--------------------------------------------------------------------------------
CREATE TEMP TABLE all_features AS
SELECT
    ST_GeomFromWKB(geometry) AS geom,
    properties AS tags
FROM read_parquet('data.parquet');

--------------------------------------------------------------------------------
-- STEP 3: Create Master Node Table (The 'nodesIndex')
-- This is the most critical step for de-duplication.
-- 1. Get ALL unique coordinates from ALL geometries.
-- 2. Get the tags from ONLY the POINT geometries.
-- 3. Join them, giving tags to points that have them.
--------------------------------------------------------------------------------

-- 3a. Get all unique vertices from ALL geometries
CREATE TEMP TABLE all_unique_coords AS
SELECT DISTINCT
    ST_Y(dp.geom) AS lat,
    ST_X(dp.geom) AS lon
FROM all_features, ST_DumpPoints(all_features.geom) AS dp;

-- 3b. Get tags from POINT features
CREATE TEMP TABLE point_tags AS
SELECT
    ST_Y(geom) AS lat,
    ST_X(geom) AS lon,
    tags
FROM all_features
WHERE ST_GeomType(geom) = 'ST_Point';

-- 3c. Create master node table. This is our 'nodes' list and 'nodesIndex'.
CREATE TEMP TABLE osm_nodes AS
SELECT
    nextval('osm_node_id_seq') AS id,
    coords.lat,
    coords.lon,
    -- Use point tags if they exist, otherwise an empty map
    COALESCE(pt.tags, MAP()) AS tags
FROM all_unique_coords AS coords
LEFT JOIN point_tags AS pt
    ON coords.lat = pt.lat AND coords.lon = pt.lon;

-- 3d. Create an index for fast lookups (optional, but good practice)
CREATE UNIQUE INDEX node_coord_idx ON osm_nodes (lat, lon);

--------------------------------------------------------------------------------
-- STEP 4: Create WAYS (from LineStrings and SIMPLE Polygons)
-- This matches the `processLineString` logic and the simple polygon case.
-- A "simple" polygon has no interior rings (holes).
--------------------------------------------------------------------------------

-- 4a. Select features that will become ways
CREATE TEMP TABLE features_for_ways AS
SELECT
    nextval('osm_way_id_seq') AS id,
    tags,
    -- Get the geometry to dump: exterior ring for polygons, or the line itself
    CASE
        WHEN ST_GeomType(geom) = 'ST_Polygon' THEN ST_ExteriorRing(geom)
        ELSE geom
    END AS way_geom
FROM all_features
WHERE 
    ST_GeomType(geom) = 'ST_LineString'
    OR (ST_GeomType(geom) = 'ST_Polygon' AND ST_NumInteriorRings(geom) = 0);

-- 4b. This table holds the way metadata (tags)
CREATE TEMP TABLE osm_ways (
    id BIGINT PRIMARY KEY,
    tags MAP(VARCHAR, VARCHAR)
);
INSERT INTO osm_ways (id, tags)
SELECT id, tags FROM features_for_ways;

-- 4c. This table holds the node references for the ways ('<nd ref=...>')
CREATE TEMP TABLE osm_way_nds AS
SELECT
    fw.id AS way_id,
    n.id AS node_id,
    dp.path[1] AS nd_order -- ST_DumpPoints path is the vertex index
FROM features_for_ways AS fw,
     ST_DumpPoints(fw.way_geom) AS dp
JOIN osm_nodes AS n
     ON n.lat = ST_Y(dp.geom) AND n.lon = ST_X(dp.geom);

--------------------------------------------------------------------------------
-- STEP 5: Create RELATIONS (from MultiPolygons and COMPLEX Polygons)
-- This matches the `processMultiPolygon` logic for "multipolygon" types.
-- A "complex" polygon has interior rings (holes).
--------------------------------------------------------------------------------

-- 5a. Select features that will become relations
CREATE TEMP TABLE features_for_relations AS
SELECT
    nextval('osm_relation_id_seq') AS id,
    geom,
    tags || MAP('type', 'multipolygon') AS tags -- Add type=multipolygon
FROM all_features
WHERE
    ST_GeomType(geom) = 'ST_MultiPolygon'
    OR (ST_GeomType(geom) = 'ST_Polygon' AND ST_NumInteriorRings(geom) > 0);

-- 5b. This table holds the relation metadata (tags)
CREATE TEMP TABLE osm_relations (
    id BIGINT PRIMARY KEY,
    tags MAP(VARCHAR, VARCHAR)
);
INSERT INTO osm_relations (id, tags)
SELECT id, tags FROM features_for_relations;

-- 5c. Dump all individual polygons from the relation features
CREATE TEMP TABLE relation_polygons AS
SELECT
    r.id AS relation_id,
    (ST_Dump(r.geom)).geom AS polygon_geom
FROM features_for_relations AS r;

-- 5d. Create "outer" ways from the exterior rings
CREATE TEMP TABLE relation_outer_rings AS
SELECT
    nextval('osm_way_id_seq') AS way_id,
    rp.relation_id,
    ST_ExteriorRing(rp.polygon_geom) AS ring_geom
FROM relation_polygons AS rp;

-- 5e. Create "inner" ways from the interior rings
CREATE TEMP TABLE relation_inner_rings AS
SELECT
    nextval('osm_way_id_seq') AS way_id,
    rp.relation_id,
    (rings.geom) AS ring_geom
FROM relation_polygons AS rp,
     LATERAL (
        -- Use generate_series to loop from 1 to N_rings
        SELECT ST_InteriorRingN(rp.polygon_geom, g.i) AS geom
        FROM generate_series(1, ST_NumInteriorRings(rp.polygon_geom)) AS g(i)
     ) AS rings;

-- 5f. Add these new ways (outer and inner) to the main osm_ways table
-- These ways have EMPTY tags, matching the JS logic.
INSERT INTO osm_ways (id, tags)
SELECT way_id, MAP() FROM relation_outer_rings;

INSERT INTO osm_ways (id, tags)
SELECT way_id, MAP() FROM relation_inner_rings;

-- 5g. Add the node references for these NEW ways to osm_way_nds
INSERT INTO osm_way_nds (way_id, node_id, nd_order)
SELECT
    rings.way_id,
    n.id AS node_id,
    dp.path[1] AS nd_order
FROM (
    SELECT * FROM relation_outer_rings
    UNION ALL
    SELECT * FROM relation_inner_rings
) AS rings,
ST_DumpPoints(rings.ring_geom) AS dp
JOIN osm_nodes AS n
     ON n.lat = ST_Y(dp.geom) AND n.lon = ST_X(dp.geom);

-- 5h. Finally, create the relation members table ('<member type=...>')
CREATE TEMP TABLE osm_relation_members AS
SELECT
    relation_id,
    way_id,
    'way' AS type,
    'outer' AS role
FROM relation_outer_rings
UNION ALL
SELECT
    relation_id,
    way_id,
    'way' AS type,
    'inner' AS role
FROM relation_inner_rings;

--------------------------------------------------------------------------------
-- STEP 6: Generate the OSM XML File
-- This is the equivalent of the `jxon.jsToString` part.
-- We build the XML line-by-line using string concatenation and a
-- massive, ordered UNION ALL query.
--------------------------------------------------------------------------------

-- 6a. Helper macro to generate <tag k=".." v=".." /> elements from a MAP
CREATE OR REPLACE MACRO generate_tags(tags_map) AS
list_transform(
    map_entries(tags_map),
    e -> '    <tag k="' || e.key || '" v="' || e.value || '" />'
);

-- 6b. Run the final query and COPY the output to a file
-- The (FORMAT 'text') with no header, quote, or delimiter just prints
-- the raw first column ('xml_line') to the file.
COPY (
    -- We use sort keys to guarantee the final output order
    SELECT xml_line FROM (
        -- 1. Header
        SELECT 1 AS sort_key1, 0 AS sort_key2, 0 AS sort_key3,
                '<?xml version="1.0" encoding="UTF-8"?>' AS xml_line
        UNION ALL
        SELECT 1, 0, 1,
                '<osm version="0.6" generator="DuckDB-Parquet-2-OSM">' AS xml_line
        
        -- 2. Nodes
        UNION ALL
        SELECT 2 AS sort_key1, n.id AS sort_key2, 0 AS sort_key3,
                '  <node id="' || n.id || '" lat="' || n.lat || '" lon="' || n.lon || '">' AS xml_line
        FROM osm_nodes AS n
        UNION ALL
        SELECT 2 AS sort_key1, n.id AS sort_key2, 1 AS sort_key3,
                tag_xml AS xml_line
        FROM osm_nodes AS n,
                UNNEST(generate_tags(n.tags)) AS t(tag_xml)
        WHERE map_cardinality(n.tags) > 0
        UNION ALL
        SELECT 2 AS sort_key1, n.id AS sort_key2, 2 AS sort_key3,
                '  </node>' AS xml_line
        FROM osm_nodes AS n

        -- 3. Ways
        UNION ALL
        SELECT 3 AS sort_key1, w.id AS sort_key2, 0 AS sort_key3,
                '  <way id="' || w.id || '">' AS xml_line
        FROM osm_ways AS w
        UNION ALL
        SELECT 3 AS sort_key1,
                nd.way_id AS sort_key2,
                1000 + nd.nd_order AS sort_key3, -- Nds come after <way>, ordered by nd_order
                '    <nd ref="' || nd.node_id || '" />' AS xml_line
        FROM osm_way_nds AS nd
        UNION ALL
        SELECT 3 AS sort_key1, w.id AS sort_key2, 2000 AS sort_key3, -- Tags come after Nds
                tag_xml AS xml_line
        FROM osm_ways AS w,
                UNNEST(generate_tags(w.tags)) AS t(tag_xml)
        WHERE map_cardinality(w.tags) > 0
        UNION ALL
        SELECT 3 AS sort_key1, w.id AS sort_key2, 9999 AS sort_key3,
                '  </way>' AS xml_line
        FROM osm_ways AS w

        -- 4. Relations
        UNION ALL
        SELECT 4 AS sort_key1, r.id AS sort_key2, 0 AS sort_key3,
                '  <relation id="' || r.id || '">' AS xml_line
        FROM osm_relations AS r
        UNION ALL
        SELECT 4 AS sort_key1,
                m.relation_id AS sort_key2,
                -- Members come after <relation>, ordered by role ('outer' first)
                1000 + ROW_NUMBER() OVER (PARTITION BY m.relation_id ORDER BY m.role DESC, m.way_id) AS sort_key3,
                '    <member type="' || m.type || '" ref="' || m.way_id || '" role="' || m.role || '" />' AS xml_line
        FROM osm_relation_members AS m
        UNION ALL
        SELECT 4 AS sort_key1, r.id AS sort_key2, 2000 AS sort_key3, -- Tags come after members
                tag_xml AS xml_line
        FROM osm_relations AS r,
                UNNEST(generate_tags(r.tags)) AS t(tag_xml)
        WHERE map_cardinality(r.tags) > 0
        UNION ALL
        SELECT 4 AS sort_key1, r.id AS sort_key2, 9999 AS sort_key3,
                '  </relation>' AS xml_line
        FROM osm_relations AS r

        -- 5. Footer
        UNION ALL
        SELECT 9 AS sort_key1, 0 AS sort_key2, 0 AS sort_key3,
                '</osm>' AS xml_line
    ) AS all_xml
    ORDER BY sort_key1, sort_key2, sort_key3
) TO 'output.osm' (FORMAT 'text', HEADER false, QUOTE '', DELIMITER '');

-- 6c. Print a success message
SELECT 'Success! Wrote OSM data to output.osm' AS message;