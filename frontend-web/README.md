# Frontend Web Application

Modern web-based UI for TerraSim using React, TypeScript, and Vite.

## Setup

```bash
npm install
npm run dev
```

## Project Structure

- `src/components/` - Reusable React components
  - `Layout/` - Main layout components (Sidebar, Toolbar)
  - `GIS/` - GIS visualization components
  - `Analysis/` - Analysis controls and forms
  - `3D/` - 3D visualization (Cesium)
  - `Common/` - Common UI components
- `src/pages/` - Page components (route targets)
- `src/services/` - API and business logic
- `src/hooks/` - Custom React hooks
- `src/store/` - State management (Zustand/Redux)
- `src/styles/` - Global styles and theme

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript type checker
- `npm run test` - Run unit tests
- `npm run test:coverage` - Run tests with coverage report
- `npm run format` - Format code with Prettier

## Environment Variables

Create `.env.local`:

```env
VITE_API_URL=http://localhost:8000
VITE_MAP_STYLE=https://...
VITE_CESIUM_KEY=your-key-here
```

## Documentation

See [../docs/UI_DESIGN.md](../docs/UI_DESIGN.md) for detailed architecture and component documentation.
