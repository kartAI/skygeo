import com.onthegomap.planetiler.Planetiler;
import com.onthegomap.planetiler.reader.SourceFeature;
import com.onthegomap.planetiler.features.FeatureCollector;
import com.onthegomap.planetiler.util.GpkgUtil;

import java.nio.file.Path;
import java.util.List;

/**
 * Planetiler profile for:
 *   N5000_Arealdekke_omrade.parquet
 *
 * Reads GeoParquet → outputs vector tiles (PMTiles + MBTiles)
 *
 * Modeled after the Overture Planetiler examples.
 */
public class N5000Arealdekke implements Planetiler.Profile {

    public static void main(String[] args) throws Exception {
        var parquetPath = Path.of("N5000_Arealdekke_omrade.parquet");

        Planetiler.create(new N5000Arealdekke())
            .addGeoParquetSource("arealdekke", parquetPath)
            .setOutputPmtiles(Path.of("n5000_arealdekke.pmtiles"))
            .setOutputMbtiles(Path.of("n5000_arealdekke.mbtiles"))
            .build()
            .run();
    }

    // You can tweak these if you want
    private static final int MIN_ZOOM = 0;
    private static final int MAX_ZOOM = 14;

    @Override
    public void processFeature(SourceFeature feature, FeatureCollector features) {

        // Skip invalid geometry (rare)
        if (!feature.canBePolygon()) {
            return;
        }

        var out = features.polygon("arealdekke")
            .inheritAttrsFrom(feature)
            .setMinZoom(MIN_ZOOM)
            .setMaxZoom(MAX_ZOOM);

        // OPTIONAL: choose attributes to propagate
        copyAttribute(feature, out, "AREALKODE");
        copyAttribute(feature, out, "AREALTYPE");
        copyAttribute(feature, out, "NAVN");
        copyAttribute(feature, out, "KVALITET");
        copyAttribute(feature, out, "OPPHAV");
        copyAttribute(feature, out, "OPPDATERINGSDATO");

        // Simplification rules (like Overture polygon profiles)
        out.setBufferPixels(pixelsForZoom());
    }

    /** Planetiler requires a zoom-dependent buffer for polygon artifacts */
    private int pixelsForZoom() {
        return 4; // good default for polygon-only layers
    }

    private void copyAttribute(SourceFeature in, FeatureCollector.Feature out, String key) {
        if (in.hasTag(key)) {
            out.setAttr(key, in.getString(key));
        }
    }

    /** Feature layers registered here */
    @Override
    public List<FeatureCollector.Layer> layers(FeatureCollector.Factory factory) {
        return List.of(
            factory.polygonLayer("arealdekke")
                .minZoom(MIN_ZOOM)
                .maxZoom(MAX_ZOOM)
        );
    }
}
