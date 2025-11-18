'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { getCollection, getCollectionItems, STACCollection, STACItem } from '@/lib/stac-client';
import ItemList from '@/components/ItemList';
import MapView from '@/components/MapView';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, RefreshCw, AlertCircle } from 'lucide-react';

export default function CollectionPage() {
  const params = useParams();
  const collectionId = params.id as string;
  
  const [collection, setCollection] = useState<STACCollection | null>(null);
  const [items, setItems] = useState<STACItem[]>([]);
  const [selectedItem, setSelectedItem] = useState<STACItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const [collectionData, itemsData] = await Promise.all([
          getCollection(collectionId),
          getCollectionItems(collectionId)
        ]);
        
        setCollection(collectionData);
        setItems(itemsData.features);
      } catch (err) {
        setError('Kunne ikke laste collection data');
        console.error('Error loading collection:', err);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [collectionId]);

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-12">
        <div className="flex flex-col items-center justify-center space-y-4">
          <RefreshCw className="h-12 w-12 animate-spin text-primary" />
          <p className="text-muted-foreground">Laster collection...</p>
        </div>
      </div>
    );
  }

  if (error || !collection) {
    return (
      <div className="container mx-auto px-4 py-12">
        <Card className="p-6 border-destructive">
          <div className="flex items-start gap-4">
            <AlertCircle className="h-5 w-5 text-destructive mt-0.5" />
            <div className="flex-1">
              <p className="font-medium text-destructive mb-4">
                {error || 'Collection ikke funnet'}
              </p>
              <Link href="/">
                <Button variant="outline">
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Tilbake til collections
                </Button>
              </Link>
            </div>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-6">
        <Link href="/">
          <Button variant="ghost" className="mb-4">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Tilbake til collections
          </Button>
        </Link>
        <h1 className="text-4xl font-bold mb-2">{collection.title}</h1>
        <p className="text-muted-foreground">{collection.description}</p>
        
        {collection.keywords && collection.keywords.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-4">
            {collection.keywords.map((keyword) => (
              <Badge key={keyword} variant="secondary">
                {keyword}
              </Badge>
            ))}
          </div>
        )}
      </div>

      {/* Stats */}
      <Card className="mb-6">
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <p className="text-sm text-muted-foreground mb-1">Antall items</p>
              <p className="text-2xl font-bold">{items.length}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground mb-1">Spatial extent</p>
              <p className="text-sm font-mono">
                {collection.extent.spatial.bbox[0]?.map(n => n.toFixed(2)).join(', ')}
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground mb-1">Lisens</p>
              <p className="text-sm">{collection.license}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Content */}
      {items.length === 0 ? (
        <Card className="p-12">
          <div className="text-center text-muted-foreground">
            <p className="text-lg">Ingen items i denne collection</p>
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Items List */}
          <div className="space-y-4">
            <h2 className="text-xl font-semibold">
              Items ({items.length})
            </h2>
            <div className="max-h-[800px] overflow-y-auto pr-2">
              <ItemList
                items={items}
                onItemClick={setSelectedItem}
                selectedItemId={selectedItem?.id}
              />
            </div>
          </div>

          {/* Map */}
          <div className="space-y-4">
            <h2 className="text-xl font-semibold">Kart</h2>
            <Card className="overflow-hidden">
              <div className="h-[700px]">
                <MapView
                  items={items}
                  selectedItem={selectedItem || undefined}
                  onItemClick={setSelectedItem}
                />
              </div>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
