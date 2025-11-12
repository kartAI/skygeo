'use client';

import { STACCollection } from '@/lib/stac-client';
import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { MapPin } from 'lucide-react';

interface CollectionCardProps {
  collection: STACCollection;
}

export default function CollectionCard({ collection }: CollectionCardProps) {
  const formatIcons: Record<string, string> = {
    cog: '🗺️',
    geoparquet: '📦',
    flatgeobuf: '📍',
    pmtiles: '🗂️',
    copc: '☁️'
  };

  const icon = formatIcons[collection.id] || '📁';

  return (
    <Link href={`/collections/${collection.id}`} className="block transition-transform hover:scale-[1.02]">
      <Card className="h-full hover:shadow-lg transition-shadow">
        <CardHeader>
          <div className="flex items-start gap-3">
            <div className="text-3xl">{icon}</div>
            <div className="flex-1">
              <CardTitle className="text-lg mb-1">{collection.title}</CardTitle>
              <CardDescription>{collection.description}</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {collection.keywords && collection.keywords.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-4">
              {collection.keywords.map((keyword) => (
                <Badge key={keyword} variant="secondary">
                  {keyword}
                </Badge>
              ))}
            </div>
          )}
          <div className="flex items-start gap-2 text-sm text-muted-foreground">
            <MapPin className="h-4 w-4 mt-0.5 flex-shrink-0" />
            <div>
              <span className="font-medium">Spatial extent:</span>{' '}
              {collection.extent.spatial.bbox[0]?.slice(0, 2).map(n => n.toFixed(2)).join(', ')} →{' '}
              {collection.extent.spatial.bbox[0]?.slice(2, 4).map(n => n.toFixed(2)).join(', ')}
            </div>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
