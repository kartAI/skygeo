import AssetActionPlugin from "../AssetActionPlugin";
import URI from 'urijs';
import i18n from "../../i18n";

// obj & ply files are usually with mime-type text/plain
const PROTOMAPS_SUPPORTED_TYPES = [
  'application/vnd.pmtiles',
];

// Viewer override: the viewer rewrites asset hrefs to its own signing proxy
// (<viewer-origin>/s3/<key>). pmtiles.io is an EXTERNAL viewer that runs in the
// browser and fetches the archive itself, so it can't use that proxy URL (it would
// hit the viewer's localhost/ingress origin, which it can't reach/authenticate).
// Map the proxied href back to the real S3 URL (<endpoint>/<bucket>/<key>), which
// the user's machine can reach directly. s3Base is injected via /config.js.
function toS3Url(href) {
  const cfg = (typeof window !== 'undefined' && window.STAC_BROWSER_CONFIG) || {};
  const base = cfg.s3Base; // e.g. https://s3.example.no/my-bucket/
  if (!base || typeof href !== 'string') {
    return href;
  }
  const marker = '/s3/';
  const idx = href.indexOf(marker);
  if (idx === -1) {
    return href; // not a proxied asset href — leave as-is
  }
  const key = href.substring(idx + marker.length);
  return (base.endsWith('/') ? base : base + '/') + key;
}

export default class Protomaps extends AssetActionPlugin {

  get show() {
    // Rather check if .pmtiles substring present in this.asset.href or simply this.component.filename.endsWith('pmtiles')
    return this.component.isBrowserProtocol && (
      PROTOMAPS_SUPPORTED_TYPES.includes(this.asset.type)
      ||  URI(this.asset.href).suffix() == 'pmtiles'
    );
  }

  get uri() {
    let uri = new URI("https://pmtiles.io/");
    uri.addQuery("url", toS3Url(this.component.href)); // real S3 URL, not the proxy
    return uri;
  }

  get text() {
    return i18n.t('actions.openIn', {service: 'Protomaps'});
  }

}
