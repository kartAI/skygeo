<!--
  Viewer override of STAC Browser v4.0.1 src/views/Item.vue.
  PINNED to v4.0.1 — re-sync this file if STAC_BROWSER_VERSION in the Dockerfile changes.

  Deltas vs upstream:
  - Lazy "Data preview" <b-tab> (shown when the item has a PMTiles asset) mounting
    <MapLibrePreview> — an inline MapLibre map of the item's data.
  - Layout: the map is a FULL-WIDTH section on top (tall, ~top half), and all the rest
    (description, collection, providers, assets, links, metadata) flows full-width BELOW it,
    so the metadata gets the whole page width (multi-column). Upstream put the map in a 50%
    left column with metadata squeezed beside it.
  - b-tabs is horizontal (`end` = pills below the map), with even pill alignment.
-->
<template>
  <div class="item" :key="data.id">
    <section class="mb-4">
      <b-card no-body class="maps-preview">
        <b-tabs v-model="tab" ref="tabs" card pills end>
          <b-tab :title="$t('map')" no-body>
            <Map :stac="data" :assets="selectedAssets" @changed="dataChanged" @empty="handleEmptyMap" />
          </b-tab>
          <b-tab v-if="hasPmtiles" title="Data preview" no-body lazy>
            <MapLibrePreview :item="data" />
          </b-tab>
          <b-tab v-if="hasThumbnails" :title="$t('thumbnails')" no-body>
            <Thumbnails :thumbnails="thumbnails" />
          </b-tab>
        </b-tabs>
      </b-card>
    </section>
    <section class="intro">
      <h2 v-if="data.properties.description">{{ $t('description') }}</h2>
      <DeprecationNotice v-if="showDeprecation" :data="data" />
      <AnonymizedNotice v-if="data.properties['anon:warning']" :warning="data.properties['anon:warning']" />
      <ReadMore v-if="data.properties.description" :lines="10" :text="$t('read.more')" :text-less="$t('read.less')">
        <Description :description="data.properties.description" />
      </ReadMore>
      <Keywords v-if="Array.isArray(data.properties.keywords) && data.properties.keywords.length > 0" :keywords="data.properties.keywords" class="mb-3" />
    </section>
    <CollectionLink v-if="collectionLink" :link="collectionLink" />
    <Providers v-if="data.properties.providers" :providers="data.properties.providers" />
    <Assets v-if="hasAssets" :assets="assets" :context="data" :shown="selectedReferences" @showAsset="showAsset" />
    <Links v-if="additionalLinks.length > 0" :title="$t('additionalResources')" :links="additionalLinks" :context="data" />
    <Metadata :data="data" type="Item" :ignoreFields="ignoredMetadataFields" />
  </div>
</template>

<script>
import { mapState, mapGetters } from 'vuex';
import Description from '../components/Description.vue';
import ReadMore from "vue-read-more-smooth";
import ShowAssetLinkMixin from '../components/ShowAssetLinkMixin';
import DeprecationMixin from '../components/DeprecationMixin';
import { BTabs, BTab } from 'bootstrap-vue';
import { addSchemaToDocument, createItemSchema } from '../schema-org';

const PMTILES_TYPE = 'application/vnd.pmtiles';

export default {
  name: "Item",
  components: {
    AnonymizedNotice: () => import('../components/AnonymizedNotice.vue'),
    Assets: () => import('../components/Assets.vue'),
    BTabs,
    BTab,
    CollectionLink: () => import('../components/CollectionLink.vue'),
    Description,
    DeprecationNotice: () => import('../components/DeprecationNotice.vue'),
    Keywords: () => import('../components/Keywords.vue'),
    Links: () => import('../components/Links.vue'),
    Map: () => import('../components/Map.vue'),
    MapLibrePreview: () => import('../components/MapLibrePreview.vue'),
    Metadata: () => import('../components/Metadata.vue'),
    Providers: () => import('../components/Providers.vue'),
    ReadMore,
    Thumbnails: () => import('../components/Thumbnails.vue')
  },
  mixins: [
    ShowAssetLinkMixin,
    DeprecationMixin
  ],
  data() {
    return {
      ignoredMetadataFields: [
        'description',
        'keywords',
        'providers',
        'title',
        // Will be rendered with a custom rendered
        'deprecated',
        // Don't show these complex lists of coordinates: https://github.com/radiantearth/stac-browser/issues/141
        'proj:bbox',
        'proj:geometry',
        // Special handling for auth
        'auth:schemes',
        // Special handling for the warning of the anonymized-location extension
        'anon:warning'
      ]
    };
  },
  computed: {
    ...mapState(['data', 'url']),
    ...mapGetters(['collectionLink', 'parentLink']),
    // show the MapLibre "Data preview" tab only when a PMTiles asset exists.
    hasPmtiles() {
      const assets = (this.data && this.data.assets) || {};
      return Object.values(assets).some(a =>
        a && typeof a.href === 'string' &&
        (a.type === PMTILES_TYPE || a.href.toLowerCase().endsWith('.pmtiles'))
      );
    }
  },
  watch: {
    data: {
      immediate: true,
      handler(data) {
        try {
          let schema = createItemSchema(data, [this.collectionLink, this.parentLink], this.$store);
          addSchemaToDocument(document, schema);
        } catch (error) {
          console.error(error);
        }
      }
    }
  }
};
</script>

<style lang="scss">
@import '~bootstrap/scss/mixins';
@import "../theme/variables.scss";

#stac-browser .item {
  // Full-width map filling roughly the top half of the viewport.
  .maps-preview .map,
  .maps-preview .maplibre-map {
    height: 60vh;
  }

  // Horizontal pills below the map — center them and undo the vertical-tab margins
  // (upstream maps-preview adds top/bottom margins meant for vertical tabs, which
  // leave the pills at uneven heights when laid out horizontally).
  .maps-preview .nav-pills {
    align-items: center;

    > li {
      margin-top: 0.5rem !important;
      margin-bottom: 0.5rem !important;
    }
  }

  // Metadata now spans the full page width below the map → use it with more columns.
  .metadata .card-columns {
    column-count: 1;

    @include media-breakpoint-up(md) {
      column-count: 2;
    }
    @include media-breakpoint-up(xxl) {
      column-count: 3;
    }
  }
}
</style>
