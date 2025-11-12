'use client';

import { useEffect, useRef, useState } from 'react';
import dynamic from 'next/dynamic';
import type { Map as LeafletMap } from 'leaflet';
import { STACItem } from '@/lib/stac-client';

interface MapViewProps {
  items: STACItem[];
  selectedItem?: STACItem;
  onItemClick?: (item: STACItem) => void;
}

// Dynamically import map components to avoid SSR issues
const MapContainer = dynamic(
  () => import('react-leaflet').then((mod) => mod.MapContainer),
  { ssr: false }
);

const TileLayer = dynamic(
  () => import('react-leaflet').then((mod) => mod.TileLayer),
  { ssr: false }
);

const GeoJSON = dynamic(
  () => import('react-leaflet').then((mod) => mod.GeoJSON),
  { ssr: false }
);

// Component to fit bounds when items change
function FitBounds({ items }: { items: STACItem[] }) {
  const { useMap } = require('react-leaflet');
  const map = useMap();
  
  useEffect(() => {
    if (items.length > 0) {
      const bounds = items
        .filter(item => item.bbox)
        .map(item => [
          [item.bbox[1], item.bbox[0]],
          [item.bbox[3], item.bbox[2]]
        ] as [[number, number], [number, number]]);
      
      if (bounds.length > 0) {
        const allBounds = bounds.reduce((acc, bound) => {
          if (!acc) return bound;
          return [
            [Math.min(acc[0][0], bound[0][0]), Math.min(acc[0][1], bound[0][1])],
            [Math.max(acc[1][0], bound[1][0]), Math.max(acc[1][1], bound[1][1])]
          ] as [[number, number], [number, number]];
        });
        
        try {
          map.fitBounds(allBounds, { padding: [50, 50] });
        } catch (error) {
          console.error('Error fitting bounds:', error);
        }
      }
    }
  }, [items, map]);
  
  return null;
}

export default function MapView({ items, selectedItem, onItemClick }: MapViewProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-gray-100">
        <p className="text-gray-500">Laster kart...</p>
      </div>
    );
  }

  const itemsWithGeometry = items.filter(item => item.geometry && item.bbox);

  if (itemsWithGeometry.length === 0) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-gray-100">
        <p className="text-gray-500">Ingen geometrier å vise</p>
      </div>
    );
  }

  return (
    <MapContainer
      center={[60, 10]}
      zoom={5}
      style={{ width: '100%', height: '100%' }}
      className="z-0"
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      
      {itemsWithGeometry.map((item) => (
        <GeoJSON
          key={item.id}
          data={item.geometry}
          style={{
            fillColor: selectedItem?.id === item.id ? '#0ea5e9' : '#3b82f6',
            fillOpacity: selectedItem?.id === item.id ? 0.4 : 0.2,
            color: selectedItem?.id === item.id ? '#0284c7' : '#2563eb',
            weight: selectedItem?.id === item.id ? 3 : 2,
          }}
          eventHandlers={{
            click: () => onItemClick?.(item),
          }}
        />
      ))}
      
      <FitBounds items={itemsWithGeometry} />
    </MapContainer>
  );
}
