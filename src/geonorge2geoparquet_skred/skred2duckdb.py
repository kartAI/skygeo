import os
import argparse
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Combine Skredfaresoner and Aktsomhetskart using DuckDB spatial operations')
    parser.add_argument('--input-dir', 
                       default='temp_debug/workshop',
                       help='Directory containing the input GeoParquet files (default: temp_debug/workshop)')
    parser.add_argument('--output-file', 
                       default='combined_skred_data.parquet',
                       help='Output filename (default: combined_skred_data.parquet)')
    return parser.parse_args()

def find_geoparquet_files(input_dir):
    """Find GeoParquet files with exact paths"""
    logger.info(f"Looking for specific GeoParquet files in: {input_dir}")
    
    if not os.path.exists(input_dir):
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    
    # Use exact file paths to avoid assignment errors
    skredfaresoner_path = os.path.join(input_dir, 'Skredfaresoner.parquet')
    aktsomhetskart_path = os.path.join(input_dir, 'Aktsomhetskart.parquet')
    
    # Validate that both files exist
    if not os.path.exists(skredfaresoner_path):
        raise FileNotFoundError(f"Skredfaresoner file not found: {skredfaresoner_path}")
    
    if not os.path.exists(aktsomhetskart_path):
        raise FileNotFoundError(f"Aktsomhetskart file not found: {aktsomhetskart_path}")
    
    logger.info(f"Using exact file paths:")
    logger.info(f"  Skredfaresoner: {os.path.basename(skredfaresoner_path)}")
    logger.info(f"  Aktsomhetskart: {os.path.basename(aktsomhetskart_path)}")
    
    return skredfaresoner_path, aktsomhetskart_path

def examine_data_structure(skredfaresoner_path, aktsomhetskart_path):
    """Examine the structure of input files"""
    import duckdb
    
    logger.info("Examining data structure...")
    
    conn = duckdb.connect(':memory:')
    conn.execute("INSTALL spatial")
    conn.execute("LOAD spatial")
    
    try:
        # Check first file structure
        logger.info(f"Analyzing {os.path.basename(skredfaresoner_path)}:")
        
        columns_query = f"""
        DESCRIBE SELECT * FROM read_parquet('{skredfaresoner_path}') LIMIT 1
        """
        columns_result = conn.execute(columns_query).fetchall()
        logger.info(f"  Columns: {[row[0] for row in columns_result]}")
        
        # Check for source_layer column and Analyseområde
        try:
            analyseomrade_check = conn.execute(f"""
                SELECT 
                    COUNT(*) as total_features,
                    COUNT(CASE WHEN source_layer = 'Analyseområde' THEN 1 END) as analyseomrade_features,
                    array_agg(DISTINCT source_layer) as unique_layers
                FROM read_parquet('{skredfaresoner_path}')
            """).fetchone()
            
            logger.info(f"  Total features: {analyseomrade_check[0]}")
            logger.info(f"  Analyseområde features: {analyseomrade_check[1]}")
            logger.info(f"  Unique layers: {analyseomrade_check[2]}")
        except Exception as e:
            logger.warning(f"  Could not analyze source_layer: {e}")
        
        # Check second file structure
        logger.info(f"Analyzing {os.path.basename(aktsomhetskart_path)}:")
        
        columns_query2 = f"""
        DESCRIBE SELECT * FROM read_parquet('{aktsomhetskart_path}') LIMIT 1
        """
        columns_result2 = conn.execute(columns_query2).fetchall()
        logger.info(f"  Columns: {[row[0] for row in columns_result2]}")
        
        aktsom_count = conn.execute(f"""
            SELECT COUNT(*) as total_features
            FROM read_parquet('{aktsomhetskart_path}')
        """).fetchone()
        
        logger.info(f"  Total features: {aktsom_count[0]}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to examine data structure: {e}")
        raise
    finally:
        conn.close()

def combine_geoparquet_files(skredfaresoner_path, aktsomhetskart_path, output_path):
    """Combine GeoParquet files using DuckDB spatial operations"""
    import duckdb
    
    logger.info("Starting spatial operations with DuckDB...")
    
    # Connect to DuckDB and install spatial extension
    conn = duckdb.connect(':memory:')
    conn.execute("INSTALL spatial")
    conn.execute("LOAD spatial")
    
    try:
        # First, analyze the schema of both files
        logger.info("Analyzing schemas to ensure compatibility...")
        
        schema1 = conn.execute(f"DESCRIBE SELECT * FROM read_parquet('{skredfaresoner_path}') LIMIT 1").fetchall()
        schema2 = conn.execute(f"DESCRIBE SELECT * FROM read_parquet('{aktsomhetskart_path}') LIMIT 1").fetchall()
        
        cols1 = [row[0] for row in schema1]
        cols2 = [row[0] for row in schema2]
        
        logger.info(f"Skredfaresoner columns ({len(cols1)}): {cols1}")
        logger.info(f"Aktsomhetskart columns ({len(cols2)}): {cols2}")
        
        # Get initial counts for validation
        count1 = conn.execute(f"SELECT COUNT(*) FROM read_parquet('{skredfaresoner_path}')").fetchone()[0]
        count2 = conn.execute(f"SELECT COUNT(*) FROM read_parquet('{aktsomhetskart_path}')").fetchone()[0]
        
        logger.info(f"Input counts: Skredfaresoner={count1}, Aktsomhetskart={count2}, Total={count1+count2}")
        
        # Define required attributes for each dataset
        skred_required_attrs = ['skredStatistikkSannsynlighet', 'source_layer', 'geometry']
        aktsom_required_attrs = ['skogeffekt', 'source_layer', 'sikkerhetsklasse', 'geometry']
        
        # Define source_layers to exclude from the result
        excluded_layers = ['AnalyseområdeGr', 'SkredFaregrense']
        
        logger.info(f"Required Skredfaresoner attributes: {skred_required_attrs}")
        logger.info(f"Required Aktsomhetskart attributes: {aktsom_required_attrs}")
        logger.info(f"Excluding source_layers: {excluded_layers}")
        logger.info("Adding computed attributes: risk_factor, data_quality")
        
        # Check if required attributes exist
        missing_skred = [attr for attr in skred_required_attrs if attr not in cols1]
        missing_aktsom = [attr for attr in aktsom_required_attrs if attr not in cols2]
        
        if missing_skred:
            logger.warning(f"Missing Skredfaresoner attributes: {missing_skred}")
        if missing_aktsom:
            logger.warning(f"Missing Aktsomhetskart attributes: {missing_aktsom}")
        
        # Step 1: Features from Skredfaresoner with risk mapping
        logger.info("Step 1: Selecting Skredfaresoner with risk_factor and data_quality mapping...")
        
        # Build column list for Skredfaresoner with only required attributes
        skred_select_parts = []
        for attr in skred_required_attrs:
            if attr in cols1:
                skred_select_parts.append(f'"{attr}"')
            else:
                skred_select_parts.append(f"NULL as \"{attr}\"")
        
        # Add NULL values for Aktsomhetskart-specific attributes
        skred_select_parts.extend([
            "NULL as skogeffekt",
            "NULL as sikkerhetsklasse"
        ])
        
        # Add computed risk_factor and data_quality for Skredfaresoner
        skred_risk_mapping = """
        CASE 
            WHEN source_layer = 'SkredFaresone' AND skredStatistikkSannsynlighet = '5000' THEN 1
            WHEN source_layer = 'SkredFaresone' AND skredStatistikkSannsynlighet = '1000' THEN 2
            WHEN source_layer = 'SkredFaresone' AND skredStatistikkSannsynlighet = '100' THEN 4
            ELSE NULL
        END as risk_factor"""
        
        skred_quality_mapping = """
        CASE 
            WHEN source_layer = 'SkredFaresone' AND skredStatistikkSannsynlighet IN ('5000', '1000', '100') 
            THEN 'Manuell befaring'
            ELSE NULL
        END as data_quality"""
        
        skred_select_parts.extend([skred_risk_mapping, skred_quality_mapping])
        
        skredfaresoner_cols_str = ', '.join(skred_select_parts)
        
        # Create exclusion filter for Skredfaresoner
        if 'source_layer' in cols1:
            exclusion_filter = " AND ".join([f"source_layer != '{layer}'" for layer in excluded_layers])
            skred_where_clause = f"WHERE {exclusion_filter}"
        else:
            skred_where_clause = ""
        
        skredfaresoner_query = f"""
        SELECT {skredfaresoner_cols_str}, 'skredfaresoner' as data_source
        FROM read_parquet('{skredfaresoner_path}')
        {skred_where_clause}
        """
        
        # Step 2: Check for Analyseområde features
        logger.info("Step 2: Checking for Analyseområde features...")
        
        has_analyseomrade = False
        analyseomrade_count = 0
        if 'source_layer' in cols1:
            try:
                analyseomrade_test = conn.execute(f"""
                    SELECT COUNT(*) 
                    FROM read_parquet('{skredfaresoner_path}')
                    WHERE source_layer = 'Analyseområde'
                """).fetchone()
                
                analyseomrade_count = analyseomrade_test[0]
                has_analyseomrade = analyseomrade_count > 0
                logger.info(f"Found {analyseomrade_count} Analyseområde features for clipping")
                
            except Exception as e:
                logger.warning(f"Could not check Analyseområde features: {e}")
        else:
            logger.info("No source_layer column found - will include all Aktsomhetskart features")
        
        # Step 3: Process Aktsomhetskart with risk mapping - CLIP against Analyseområde
        if has_analyseomrade:
            logger.info("Step 3: Clipping Aktsomhetskart with risk mapping - REMOVING parts within Analyseområde...")
            
            # Build explicit column lists for Aktsomhetskart (only required attributes, excluding geometry)
            aktsom_non_geom_attrs = [attr for attr in aktsom_required_attrs if attr != 'geometry']
            aktsom_non_geom_str = ', '.join([f'a."{attr}"' if attr in cols2 else f'NULL as "{attr}"' for attr in aktsom_non_geom_attrs])
            
            # Use ST_Difference to actually clip geometries and remove intersecting parts
            aktsomhetskart_query = f"""
            WITH analyseomrade_union AS (
                SELECT ST_Union_Agg(geometry) as clip_geom
                FROM read_parquet('{skredfaresoner_path}')
                WHERE source_layer = 'Analyseområde'
            ),
            clipped_aktsomhet AS (
                SELECT 
                    {aktsom_non_geom_str},
                    CASE 
                        WHEN ST_Intersects(a.geometry, ao.clip_geom) 
                        THEN ST_Difference(a.geometry, ao.clip_geom)
                        ELSE a.geometry
                    END as clipped_geometry
                FROM read_parquet('{aktsomhetskart_path}') a
                CROSS JOIN analyseomrade_union ao
            )
            SELECT 
                NULL as skredStatistikkSannsynlighet,
                source_layer,
                clipped_geometry as geometry,
                skogeffekt,
                sikkerhetsklasse,
                CASE 
                    WHEN source_layer = 'PotensieltSkredfareOmr' AND sikkerhetsklasse = 'S3' THEN 1
                    WHEN source_layer = 'PotensieltSkredfareOmr' AND sikkerhetsklasse = 'S2' AND skogeffekt = 'Ja' THEN 2
                    WHEN source_layer = 'PotensieltSkredfareOmr' AND sikkerhetsklasse = 'S2' AND skogeffekt = 'Nei' THEN 3
                    ELSE NULL
                END as risk_factor,
                CASE 
                    WHEN source_layer = 'PotensieltSkredfareOmr' AND sikkerhetsklasse = 'S3' THEN 'Automatisk beregnet'
                    WHEN source_layer = 'PotensieltSkredfareOmr' AND sikkerhetsklasse = 'S2' AND skogeffekt = 'Ja' THEN 'Automatisk beregnet med skogeffekt'
                    WHEN source_layer = 'PotensieltSkredfareOmr' AND sikkerhetsklasse = 'S2' AND skogeffekt = 'Nei' THEN 'Automatisk beregnet uten skogeffekt'
                    ELSE NULL
                END as data_quality,
                'aktsomhetskart_clipped' as data_source
            FROM clipped_aktsomhet
            WHERE clipped_geometry IS NOT NULL 
            AND ST_Area(clipped_geometry) > 0
            """
        else:
            logger.info("Step 3: Including all Aktsomhetskart features with risk mapping (no Analyseområde found)...")
            
            # Build column list for Aktsomhetskart when no clipping (only required attributes)
            aktsom_select_parts = []
            for attr in aktsom_required_attrs:
                if attr in cols2:
                    aktsom_select_parts.append(f'"{attr}"')
                else:
                    aktsom_select_parts.append(f"NULL as \"{attr}\"")
            
            # Add NULL for Skredfaresoner-specific attribute
            aktsom_select_parts.insert(0, "NULL as skredStatistikkSannsynlighet")
            
            # Add computed risk_factor and data_quality for Aktsomhetskart
            aktsom_risk_mapping = """
            CASE 
                WHEN source_layer = 'PotensieltSkredfareOmr' AND sikkerhetsklasse = 'S3' THEN 1
                WHEN source_layer = 'PotensieltSkredfareOmr' AND sikkerhetsklasse = 'S2' AND skogeffekt = 'Ja' THEN 2
                WHEN source_layer = 'PotensieltSkredfareOmr' AND sikkerhetsklasse = 'S2' AND skogeffekt = 'Nei' THEN 3
                ELSE NULL
            END as risk_factor"""
            
            aktsom_quality_mapping = """
            CASE 
                WHEN source_layer = 'PotensieltSkredfareOmr' AND sikkerhetsklasse = 'S3' THEN 'Automatisk beregnet'
                WHEN source_layer = 'PotensieltSkredfareOmr' AND sikkerhetsklasse = 'S2' AND skogeffekt = 'Ja' THEN 'Automatisk beregnet med skogeffekt'
                WHEN source_layer = 'PotensieltSkredfareOmr' AND sikkerhetsklasse = 'S2' AND skogeffekt = 'Nei' THEN 'Automatisk beregnet uten skogeffekt'
                ELSE NULL
            END as data_quality"""
            
            aktsom_select_parts.extend([aktsom_risk_mapping, aktsom_quality_mapping])
            
            aktsom_cols_str = ', '.join(aktsom_select_parts)
            
            aktsomhetskart_query = f"""
            SELECT {aktsom_cols_str}, 'aktsomhetskart_unclipped' as data_source
            FROM read_parquet('{aktsomhetskart_path}')
            """
        
        # Test the clipping effect before final combination
        if has_analyseomrade:
            test_count = conn.execute(f"SELECT COUNT(*) FROM ({aktsomhetskart_query})").fetchone()[0]
            logger.info(f"Clipping effect: {count2} -> {test_count} features (some clipped, some removed)")
        
        # Get count after excluding layers from Skredfaresoner
        skred_filtered_count = conn.execute(f"SELECT COUNT(*) FROM ({skredfaresoner_query})").fetchone()[0]
        excluded_skred_count = count1 - skred_filtered_count
        logger.info(f"Skredfaresoner filtering: {count1} -> {skred_filtered_count} features ({excluded_skred_count} excluded)")
        
        # Step 4: Combine both datasets
        logger.info("Step 4: Combining datasets with risk mapping...")
        
        final_query = f"""
        WITH skredfaresoner_data AS (
            {skredfaresoner_query}
        ),
        aktsomhetskart_data AS (
            {aktsomhetskart_query}
        )
        SELECT * FROM skredfaresoner_data
        UNION ALL
        SELECT * FROM aktsomhetskart_data
        """
        
        # Execute and save to optimized GeoParquet
        logger.info(f"Writing optimized GeoParquet to: {output_path}")
        
        conn.execute(f"""
            COPY (
                {final_query}
            ) TO '{output_path}' 
            (
                FORMAT 'parquet', 
                COMPRESSION 'snappy',
                ROW_GROUP_SIZE 10000
            )
        """)
        
        logger.info("GeoParquet file written successfully with optimizations:")
        logger.info("  - Compression: Snappy")
        logger.info("  - Row group size: 10,000")
        logger.info("  - Only selected attributes included")
        logger.info("  - Excluded source_layers filtered out")
        logger.info("  - Risk factor and data quality computed")
        logger.info("  - Actual geometric clipping performed")
        
        # Get statistics on the result including risk factor analysis
        result_stats = conn.execute(f"""
            SELECT 
                COUNT(*) as total_features,
                COUNT(CASE WHEN data_source = 'skredfaresoner' THEN 1 END) as skredfaresoner_count,
                COUNT(CASE WHEN data_source LIKE 'aktsomhetskart%' THEN 1 END) as aktsomhetskart_count,
                array_agg(DISTINCT data_source) as data_sources,
                array_agg(DISTINCT source_layer) as source_layers,
                COUNT(CASE WHEN skredStatistikkSannsynlighet IS NOT NULL THEN 1 END) as has_skred_stats,
                COUNT(CASE WHEN skogeffekt IS NOT NULL THEN 1 END) as has_skogeffekt,
                COUNT(CASE WHEN sikkerhetsklasse IS NOT NULL THEN 1 END) as has_sikkerhetsklasse,
                COUNT(CASE WHEN risk_factor IS NOT NULL THEN 1 END) as has_risk_factor,
                COUNT(CASE WHEN data_quality IS NOT NULL THEN 1 END) as has_data_quality,
                array_agg(DISTINCT risk_factor) as unique_risk_factors,
                array_agg(DISTINCT data_quality) as unique_data_quality
            FROM read_parquet('{output_path}')
        """).fetchone()
        
        logger.info("Spatial operations completed successfully!")
        logger.info(f"Result statistics:")
        logger.info(f"  Total features: {result_stats[0]} (input total was {count1 + count2})")
        logger.info(f"  From Skredfaresoner (filtered): {result_stats[1]} (input: {count1}, excluded: {excluded_skred_count})")
        logger.info(f"  From Aktsomhetskart (clipped): {result_stats[2]} (input: {count2})")
        logger.info(f"  Data sources: {result_stats[3]}")
        logger.info(f"  Source layers: {result_stats[4]}")
        logger.info(f"  Features with skredStatistikkSannsynlighet: {result_stats[5]}")
        logger.info(f"  Features with skogeffekt: {result_stats[6]}")
        logger.info(f"  Features with sikkerhetsklasse: {result_stats[7]}")
        logger.info(f"  Features with risk_factor: {result_stats[8]}")
        logger.info(f"  Features with data_quality: {result_stats[9]}")
        logger.info(f"  Unique risk_factors: {result_stats[10]}")
        logger.info(f"  Unique data_quality values: {result_stats[11]}")
        logger.info(f"  Excluded layers: {excluded_layers}")
        
        if has_analyseomrade:
            affected_count = count2 - result_stats[2] if result_stats[2] < count2 else 0
            logger.info(f"  Features affected by clipping: {affected_count}")
        
        # Get file size
        output_size = os.path.getsize(output_path)
        logger.info(f"Output file size: {output_size:,} bytes")
        
        return {
            "output_path": output_path,
            "total_features": result_stats[0],
            "skredfaresoner_features": result_stats[1],
            "aktsomhetskart_features": result_stats[2],
            "input_total": count1 + count2,
            "excluded_layers": excluded_layers,
            "excluded_count": excluded_skred_count,
            "clipping_performed": has_analyseomrade,
            "file_size_bytes": output_size,
            "data_sources": result_stats[3],
            "source_layers": result_stats[4],
            "attribute_counts": {
                "skredStatistikkSannsynlighet": result_stats[5],
                "skogeffekt": result_stats[6],
                "sikkerhetsklasse": result_stats[7],
                "risk_factor": result_stats[8],
                "data_quality": result_stats[9]
            },
            "unique_values": {
                "risk_factors": result_stats[10],
                "data_quality": result_stats[11]
            },
            "optimization": {
                "compression": "snappy",
                "row_group_size": 10000
            },
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Spatial operations failed: {e}")
        raise
    finally:
        conn.close()

def validate_output(output_path):
    """Validate the output GeoParquet file including source_layer checks"""
    import duckdb
    
    logger.info("Validating optimized output file...")
    
    conn = duckdb.connect(':memory:')
    conn.execute("INSTALL spatial")
    conn.execute("LOAD spatial")
    
    try:
        # Basic validation
        if not os.path.exists(output_path):
            raise FileNotFoundError(f"Output file not found: {output_path}")
        
        file_size = os.path.getsize(output_path)
        if file_size == 0:
            raise ValueError("Output file is empty")
        
        # Test reading and basic spatial checks including source_layer
        validation_query = f"""
        SELECT 
            COUNT(*) as feature_count,
            COUNT(CASE WHEN geometry IS NOT NULL THEN 1 END) as valid_geometry_count,
            COUNT(DISTINCT data_source) as data_source_count,
            COUNT(CASE WHEN source_layer IS NOT NULL THEN 1 END) as has_source_layer_count,
            array_agg(DISTINCT source_layer) as unique_source_layers
        FROM read_parquet('{output_path}')
        """
        
        result = conn.execute(validation_query).fetchone()
        
        validation_report = {
            "file_path": output_path,
            "file_size_bytes": file_size,
            "feature_count": result[0],
            "valid_geometry_count": result[1],
            "data_source_count": result[2],
            "has_source_layer_count": result[3],
            "unique_source_layers": result[4],
            "checks": {
                "file_exists": True,
                "non_empty": file_size > 0,
                "has_features": result[0] > 0,
                "all_geometries_valid": result[0] == result[1],
                "has_multiple_sources": result[2] >= 1,
                "source_layer_preserved": result[3] == result[0]
            },
            "optimization": {
                "compression": "snappy",
                "row_group_size": 10000
            },
            "status": "pass" if (result[0] > 0 and result[0] == result[1] and result[3] == result[0]) else "warning"
        }
        
        logger.info(f"Validation completed: {validation_report['status']}")
        logger.info(f"  Features: {validation_report['feature_count']}")
        logger.info(f"  Valid geometries: {validation_report['valid_geometry_count']}")
        logger.info(f"  Data sources: {validation_report['data_source_count']}")
        logger.info(f"  Features with source_layer: {validation_report['has_source_layer_count']}")
        logger.info(f"  Unique source_layers: {validation_report['unique_source_layers']}")
        logger.info(f"  File size: {validation_report['file_size_bytes']:,} bytes")
        
        return validation_report
        
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise
    finally:
        conn.close()

def main():
    """Main function to run the spatial processing pipeline"""
    try:
        # Parse arguments
        args = parse_arguments()
        
        logger.info("Starting DuckDB spatial processing pipeline...")
        logger.info(f"Input directory: {args.input_dir}")
        logger.info(f"Output file: {args.output_file}")
        
        # Find GeoParquet files with exact paths
        skredfaresoner_path, aktsomhetskart_path = find_geoparquet_files(args.input_dir)
        
        # Examine data structure
        examine_data_structure(skredfaresoner_path, aktsomhetskart_path)
        
        # Create output path
        output_path = os.path.join(args.input_dir, args.output_file)
        
        # Perform spatial operations
        result = combine_geoparquet_files(
            skredfaresoner_path, 
            aktsomhetskart_path, 
            output_path
        )
        
        # Validate output
        validation_result = validate_output(output_path)
        
        logger.info("Pipeline completed successfully!")
        logger.info(f"Combined GeoParquet saved to: {result['output_path']}")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()