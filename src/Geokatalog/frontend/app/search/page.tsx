'use client';

import { useEffect, useState } from 'react';
import { searchItems, getCollections, STACItem, STACCollection } from '@/lib/stac-client';
import SearchBar, { SearchParams } from '@/components/SearchBar';
import ItemList from '@/components/ItemList';
import MapView from '@/components/MapView';
import { Card } from '@/components/ui/card';
import { RefreshCw, AlertCircle } from 'lucide-react';

export default function SearchPage() {
  const [collections, setCollections] = useState<STACCollection[]>([]);
  const [items, setItems] = useState<STACItem[]>([]);
  const [selectedItem, setSelectedItem] = useState<STACItem | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);

  useEffect(() => {
    const loadCollections = async () => {
      try {
        const response = await getCollections();
        setCollections(response.collections);
      } catch (err) {
        console.error('Error loading collections:', err);
      }
    };

    loadCollections();
  }, []);

  const handleSearch = async (params: SearchParams) => {
    try {
      setLoading(true);
      setError(null);
      setSearched(true);
      
      const response = await searchItems(params);
      setItems(response.features);
    } catch (err) {
      setError('Søket feilet. Sjekk parametrene og prøv igjen.');
      console.error('Error searching items:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">Søk i STAC Catalog</h1>
        <p className="text-muted-foreground">
          Søk etter geospatiale items basert på bounding box, collections og andre kriterier
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Search Bar */}
        <div className="lg:col-span-1 space-y-4">
          <SearchBar
            onSearch={handleSearch}
            collections={collections.map(c => c.id)}
          />
          
          {searched && !loading && (
            <Card className="p-4">
              <p className="text-sm text-muted-foreground">
                Resultater: <span className="font-bold text-foreground">{items.length}</span>
              </p>
            </Card>
          )}
        </div>

        {/* Results */}
        <div className="lg:col-span-2 space-y-6">
          {loading && (
            <Card className="p-12">
              <div className="flex flex-col items-center justify-center space-y-4">
                <RefreshCw className="h-12 w-12 animate-spin text-primary" />
                <p className="text-muted-foreground">Søker...</p>
              </div>
            </Card>
          )}

          {error && (
            <Card className="p-6 border-destructive">
              <div className="flex items-start gap-4">
                <AlertCircle className="h-5 w-5 text-destructive mt-0.5" />
                <p className="font-medium text-destructive">{error}</p>
              </div>
            </Card>
          )}

          {!loading && !error && !searched && (
            <Card className="p-12">
              <div className="text-center text-muted-foreground">
                <p className="text-lg">
                  Bruk søkeskjemaet til venstre for å søke etter items
                </p>
              </div>
            </Card>
          )}

          {!loading && !error && searched && items.length === 0 && (
            <Card className="p-12">
              <div className="text-center text-muted-foreground">
                <p className="text-lg">
                  Ingen items funnet. Prøv å endre søkeparametrene.
                </p>
              </div>
            </Card>
          )}

          {!loading && !error && items.length > 0 && (
            <>
              {/* Map */}
              <div className="space-y-4">
                <h2 className="text-xl font-semibold">Kart</h2>
                <Card className="overflow-hidden">
                  <div className="h-[400px]">
                    <MapView
                      items={items}
                      selectedItem={selectedItem || undefined}
                      onItemClick={setSelectedItem}
                    />
                  </div>
                </Card>
              </div>

              {/* Items List */}
              <div className="space-y-4">
                <h2 className="text-xl font-semibold">
                  Items ({items.length})
                </h2>
                <div className="max-h-[600px] overflow-y-auto pr-2">
                  <ItemList
                    items={items}
                    onItemClick={setSelectedItem}
                    selectedItemId={selectedItem?.id}
                  />
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
