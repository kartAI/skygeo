# STAC Catalog Frontend

Frontend for the STAC (SpatioTemporal Asset Catalog) system built with Next.js 14 and React.

## Features

- **Collections View**: Browse all available STAC collections
- **Collection Detail**: View items within a collection with an interactive map
- **Search**: Search for items across collections with spatial filters
- **Interactive Map**: Visualize geospatial data on a Leaflet map
- **Responsive Design**: Modern UI built with Tailwind CSS

## Installation

### Prerequisites

- Node.js 18+ and npm

### Setup

1. Install dependencies:
```powershell
npm install
```

2. Create a `.env.local` file:
```
NEXT_PUBLIC_STAC_API_URL=http://localhost:8000
```

3. Start the development server:
```powershell
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Project Structure

```
frontend/
├── app/
│   ├── layout.tsx           # Root layout with navigation
│   ├── page.tsx             # Home page - collections list
│   ├── globals.css          # Global styles
│   ├── collections/
│   │   └── [id]/
│   │       └── page.tsx     # Collection detail page
│   └── search/
│       └── page.tsx         # Search page
├── components/
│   ├── CollectionCard.tsx   # Collection card component
│   ├── ItemList.tsx         # List of STAC items
│   ├── MapView.tsx          # Leaflet map component
│   └── SearchBar.tsx        # Search form component
├── lib/
│   └── stac-client.ts       # STAC API client
├── package.json             # Dependencies
├── tailwind.config.js       # Tailwind CSS configuration
└── README.md               # This file
```

## Pages

### Home Page (`/`)
- Lists all available STAC collections
- Refresh button to re-scan the data directory
- Click on a collection to view its items

### Collection Detail Page (`/collections/[id]`)
- Shows detailed information about a collection
- Lists all items in the collection
- Interactive map showing item geometries
- Click on items to highlight them on the map

### Search Page (`/search`)
- Search for items across collections
- Filter by bounding box
- Filter by collection
- Adjust result limit
- View results on map and in list

## Components

### CollectionCard
Displays a collection with its metadata, keywords, and spatial extent.

### ItemList
Shows a list of STAC items with their properties and assets.

### MapView
Interactive Leaflet map that displays item geometries. Supports:
- Auto-fitting bounds to show all items
- Click to select items
- Different styling for selected items

### SearchBar
Search form with filters for:
- Bounding box (spatial filter)
- Collection selection
- Result limit

## API Client

The `stac-client.ts` module provides functions to interact with the STAC API:
- `getCollections()` - Get all collections
- `getCollection(id)` - Get a specific collection
- `getCollectionItems(id)` - Get items from a collection
- `searchItems(params)` - Search for items
- `refreshCatalog()` - Trigger catalog refresh

## Development

### Running the Development Server
```powershell
npm run dev
```

### Building for Production
```powershell
npm run build
npm start
```

### Linting
```powershell
npm run lint
```

## Notes

- The frontend requires the backend API to be running on `http://localhost:8000`
- Update the `NEXT_PUBLIC_STAC_API_URL` environment variable to point to a different API URL
- The map uses OpenStreetMap tiles by default
- All geospatial data visualization depends on valid geometries from the STAC items

