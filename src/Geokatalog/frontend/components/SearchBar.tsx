'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Search } from 'lucide-react';

interface SearchBarProps {
  onSearch: (params: SearchParams) => void;
  collections: string[];
}

export interface SearchParams {
  bbox?: string;
  collections?: string;
  limit: number;
}

export default function SearchBar({ onSearch, collections }: SearchBarProps) {
  const [bbox, setBbox] = useState('');
  const [selectedCollections, setSelectedCollections] = useState<string[]>([]);
  const [limit, setLimit] = useState(100);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const params: SearchParams = {
      limit,
    };
    
    if (bbox.trim()) {
      params.bbox = bbox.trim();
    }
    
    if (selectedCollections.length > 0) {
      params.collections = selectedCollections.join(',');
    }
    
    onSearch(params);
  };

  const toggleCollection = (collectionId: string) => {
    setSelectedCollections(prev =>
      prev.includes(collectionId)
        ? prev.filter(id => id !== collectionId)
        : [...prev, collectionId]
    );
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Søkeparametere</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Bounding Box */}
          <div>
            <label htmlFor="bbox" className="block text-sm font-medium mb-2">
              Bounding Box (minx,miny,maxx,maxy)
            </label>
            <input
              type="text"
              id="bbox"
              value={bbox}
              onChange={(e) => setBbox(e.target.value)}
              placeholder="Eksempel: 10.0,60.0,11.0,61.0"
              className="w-full px-3 py-2 border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-ring"
            />
            <p className="mt-1 text-xs text-muted-foreground">
              Skriv inn koordinater i format: vest,sør,øst,nord
            </p>
          </div>

          {/* Collections */}
          {collections.length > 0 && (
            <div>
              <label className="block text-sm font-medium mb-2">
                Collections
              </label>
              <div className="flex flex-wrap gap-2">
                {collections.map((collection) => (
                  <Badge
                    key={collection}
                    variant={selectedCollections.includes(collection) ? "default" : "outline"}
                    className="cursor-pointer"
                    onClick={() => toggleCollection(collection)}
                  >
                    {collection}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Limit */}
          <div>
            <label htmlFor="limit" className="block text-sm font-medium mb-2">
              Maks antall resultater
            </label>
            <input
              type="number"
              id="limit"
              value={limit}
              onChange={(e) => setLimit(parseInt(e.target.value) || 100)}
              min="1"
              max="1000"
              className="w-full px-3 py-2 border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>

          {/* Submit Button */}
          <Button type="submit" className="w-full" size="lg">
            <Search className="h-4 w-4 mr-2" />
            Søk
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
