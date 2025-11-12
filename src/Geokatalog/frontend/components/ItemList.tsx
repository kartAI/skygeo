'use client';

import { STACItem } from '@/lib/stac-client';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Calendar, MapPin, Box } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ItemListProps {
  items: STACItem[];
  onItemClick?: (item: STACItem) => void;
  selectedItemId?: string;
}

export default function ItemList({ items, onItemClick, selectedItemId }: ItemListProps) {
  if (items.length === 0) {
    return (
      <Card className="p-12">
        <div className="text-center text-muted-foreground">
          <p className="text-lg">Ingen items funnet i denne collection.</p>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-3">
      {items.map((item) => (
        <Card
          key={item.id}
          onClick={() => onItemClick?.(item)}
          className={cn(
            "cursor-pointer transition-all hover:shadow-md",
            selectedItemId === item.id && "ring-2 ring-primary bg-accent"
          )}
        >
          <CardHeader className="pb-3">
            <CardTitle className="text-base">{item.id}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-2 text-sm">
              {item.properties.datetime && (
                <div className="flex items-start gap-2 text-muted-foreground">
                  <Calendar className="h-4 w-4 mt-0.5 flex-shrink-0" />
                  <span>
                    {new Date(item.properties.datetime).toLocaleDateString('no-NO')}
                  </span>
                </div>
              )}
              {item.bbox && (
                <div className="flex items-start gap-2 text-muted-foreground">
                  <MapPin className="h-4 w-4 mt-0.5 flex-shrink-0" />
                  <span className="font-mono text-xs">
                    [{item.bbox.map(n => n.toFixed(4)).join(', ')}]
                  </span>
                </div>
              )}
              {item.properties.crs && (
                <div className="flex items-start gap-2 text-muted-foreground">
                  <Box className="h-4 w-4 mt-0.5 flex-shrink-0" />
                  <span>
                    {typeof item.properties.crs === 'string' 
                      ? item.properties.crs 
                      : item.properties.crs.properties?.name || 'Unknown CRS'}
                    {typeof item.properties.crs === 'object' && item.properties.crs.properties?.description && (
                      <span className="text-xs ml-1">({item.properties.crs.properties.description})</span>
                    )}
                  </span>
                </div>
              )}
            </div>
            
            {/* Additional properties */}
            <div className="grid grid-cols-2 gap-2 pt-2 border-t text-xs text-muted-foreground">
              {item.properties.width && (
                <div><span className="font-medium">Width:</span> {item.properties.width}</div>
              )}
              {item.properties.height && (
                <div><span className="font-medium">Height:</span> {item.properties.height}</div>
              )}
              {item.properties.bands && (
                <div><span className="font-medium">Bands:</span> {item.properties.bands}</div>
              )}
              {item.properties.feature_count !== undefined && (
                <div><span className="font-medium">Features:</span> {item.properties.feature_count}</div>
              )}
              {item.properties.point_count !== undefined && (
                <div><span className="font-medium">Points:</span> {item.properties.point_count.toLocaleString()}</div>
              )}
              {item.properties.geometry_type && (
                <div><span className="font-medium">Geometry:</span> {item.properties.geometry_type}</div>
              )}
            </div>
            
            {/* Columns information for vector data */}
            {item.properties.columns && Array.isArray(item.properties.columns) && item.properties.columns.length > 0 && (
              <div className="pt-2 border-t">
                <span className="text-xs font-medium text-muted-foreground block mb-2">
                  Columns ({item.properties.columns.length}):
                </span>
                <div className="flex flex-wrap gap-1">
                  {item.properties.columns.slice(0, 5).map((col: any, idx: number) => (
                    <Badge key={idx} variant="outline" className="text-xs font-mono">
                      {typeof col === 'string' ? col : col.name}
                      {typeof col === 'object' && col.type && (
                        <span className="ml-1 text-muted-foreground">: {col.type}</span>
                      )}
                    </Badge>
                  ))}
                  {item.properties.columns.length > 5 && (
                    <Badge variant="outline" className="text-xs">
                      +{item.properties.columns.length - 5} more
                    </Badge>
                  )}
                </div>
              </div>
            )}
            
            {/* Assets */}
            {Object.keys(item.assets).length > 0 && (
              <div className="pt-2 border-t">
                <span className="text-xs font-medium text-muted-foreground block mb-2">Assets:</span>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(item.assets).map(([key, asset]) => (
                    <Badge key={key} variant="secondary" className="text-xs">
                      {key}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
