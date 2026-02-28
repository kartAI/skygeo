import fiona
import yaml
import sys
from pathlib import Path

# Usage: python create_planetiler_yaml.py <geopackage_path> <output_yaml_path>

def list_layers(geopackage_path):
    return fiona.listlayers(geopackage_path)

def get_projection(geopackage_path, layer_name):
    with fiona.open(geopackage_path, layer=layer_name) as src:
        crs = src.crs
        # Try to get EPSG code
        if crs and 'init' in crs:
            return crs['init'].upper()
        elif crs and 'epsg' in crs:
            return f"EPSG:{crs['epsg']}"
        elif crs and 'authority' in crs and 'code' in crs:
            return f"{crs['authority'].upper()}:{crs['code']}"
        return 'EPSG:25833'  # fallback

def get_layer_fields(geopackage_path, layer_name):
    with fiona.open(geopackage_path, layer=layer_name) as src:
        return list(src.schema['properties'].keys())

def build_yaml(layers, geopackage_path):
    filename = Path(geopackage_path).stem
    # Use first layer to get projection
    projection = get_projection(geopackage_path, layers[0]) if layers else 'EPSG:25833'
    schema = {
        'schema_name': filename,
        'schema_description': filename,
        'args': {
            'minzoom': 0,
            'maxzoom': 15
        },
        'sources': {
            'dataset': {
                'type': 'geopackage',
                'local_path': f"{Path(geopackage_path).name}",
                'projection': projection
            }
        },
        'layers': []
    }
    for layer in layers:
        fields = get_layer_fields(geopackage_path, layer)
        attributes = [{'key': field} for field in fields]
        schema['layers'].append({
            'id': layer,
            'features': [
                {
                    'source': 'dataset',
                    'include_when': {
                        "${ feature.source_layer }": [layer]
                    },
                    'attributes': attributes
                }
            ]
        })
    return schema

def main():
    if len(sys.argv) != 3:
        print("Usage: python create_planetiler_yaml.py <geopackage_path> <output_yaml_path>")
        sys.exit(1)
    geopackage_path = sys.argv[1]
    output_yaml_path = sys.argv[2]
    layers = list_layers(geopackage_path)
    schema = build_yaml(layers, geopackage_path)
    with open(output_yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(schema, f, allow_unicode=True, sort_keys=False)
    print(f"YAML file created: {output_yaml_path}")

if __name__ == "__main__":
    main()
