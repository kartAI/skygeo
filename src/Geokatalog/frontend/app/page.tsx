'use client';

import { useEffect, useState } from 'react';
import { getCollections, refreshCatalog, STACCollection } from '@/lib/stac-client';
import CollectionCard from '@/components/CollectionCard';
import { Button } from '@/components/ui/button';
import { RefreshCw, AlertCircle } from 'lucide-react';
import { Card } from '@/components/ui/card';

export default function Home() {
  const [collections, setCollections] = useState<STACCollection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const loadCollections = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await getCollections();
      setCollections(response.collections);
    } catch (err) {
      setError('Kunne ikke laste collections. Sjekk at backend kjører på http://localhost:8000');
      console.error('Error loading collections:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    try {
      setRefreshing(true);
      await refreshCatalog();
      await loadCollections();
    } catch (err) {
      setError('Kunne ikke oppdatere katalog');
      console.error('Error refreshing catalog:', err);
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadCollections();
  }, []);

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-12">
        <div className="flex flex-col items-center justify-center space-y-4">
          <RefreshCw className="h-12 w-12 animate-spin text-primary" />
          <p className="text-muted-foreground">Laster collections...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-12">
        <Card className="p-6 border-destructive">
          <div className="flex items-start gap-4">
            <AlertCircle className="h-5 w-5 text-destructive mt-0.5" />
            <div className="flex-1">
              <p className="font-medium text-destructive mb-2">{error}</p>
              <Button onClick={loadCollections} variant="destructive">
                Prøv igjen
              </Button>
            </div>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
        <div>
          <h1 className="text-4xl font-bold mb-2">STAC Collections</h1>
          <p className="text-muted-foreground">
            Utforsk {collections.length} collection{collections.length !== 1 ? 's' : ''} av geospatiale data
          </p>
        </div>
        <Button
          onClick={handleRefresh}
          disabled={refreshing}
          size="lg"
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
          {refreshing ? 'Oppdaterer...' : 'Oppdater katalog'}
        </Button>
      </div>

      {collections.length === 0 ? (
        <Card className="p-12">
          <div className="text-center space-y-4">
            <p className="text-lg text-muted-foreground">
              Ingen collections funnet. Legg til geospatiale filer i datamappen og oppdater katalogen.
            </p>
            <Button onClick={handleRefresh} size="lg">
              <RefreshCw className="h-4 w-4 mr-2" />
              Oppdater katalog
            </Button>
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {collections.map((collection) => (
            <CollectionCard key={collection.id} collection={collection} />
          ))}
        </div>
      )}
    </div>
  );
}

