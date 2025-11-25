# Arborescent Trust - Admin Dashboard

Modern React-based admin dashboard for managing the Arborescent Trust invite tree system.

## Features

- **Dashboard Overview**: Real-time statistics on users, invites, and system health
- **User Management**: Search, filter, flag, and investigate users
- **Tree Visualization**: Interactive D3.js tree visualization of invite relationships
- **Prune Operations**: Preview and execute surgical pruning with dry-run support
- **Audit Log**: Comprehensive audit trail with filtering and search
- **Beautiful UI**: Modern design with dark mode support using Tailwind CSS

## Tech Stack

- **React 18** with TypeScript
- **Vite** for fast development and building
- **React Router** for navigation
- **Axios** for API communication
- **D3.js** for tree visualization
- **Tailwind CSS** for styling
- **Lucide React** for icons
- **date-fns** for date formatting

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend API running on http://localhost:8000

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

The app will be available at http://localhost:5173

### Build for Production

```bash
npm run build
```

Built files will be in the `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

## Configuration

Create a `.env` file (or copy `.env.example`):

```bash
VITE_API_BASE_URL=http://localhost:8000
```

## Project Structure

```
frontend/
├── src/
│   ├── components/        # Reusable components
│   │   ├── DashboardLayout.tsx
│   │   └── TreeVisualization.tsx
│   ├── pages/            # Page components
│   │   ├── Login.tsx
│   │   ├── Register.tsx
│   │   ├── Dashboard.tsx
│   │   ├── Users.tsx
│   │   ├── TreeView.tsx
│   │   ├── PruneOperations.tsx
│   │   └── AuditLog.tsx
│   ├── lib/              # Utilities and contexts
│   │   ├── api.ts        # API client
│   │   └── auth.tsx      # Auth context
│   ├── types/            # TypeScript types
│   │   └── index.ts
│   ├── App.tsx           # Main app with routing
│   ├── main.tsx          # Entry point
│   └── index.css         # Global styles
├── public/               # Static assets
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

## Features in Detail

### Authentication

- JWT-based authentication with refresh tokens
- Token stored in localStorage
- Automatic token refresh on expiration
- Protected routes with role-based access

### Dashboard

- Real-time statistics
- User status breakdown
- Invite system metrics
- Recent activity tracking
- Health score monitoring

### User Management

- Search by username or email
- Filter by status (active, flagged, suspended, banned)
- View user details and tree
- Flag/unflag users
- Paginated results

### Tree Visualization

- Interactive D3.js tree layout
- Color-coded nodes by health score
- Click to view node details
- Navigate between user trees
- Responsive design

### Prune Operations

- Dry-run preview before execution
- Shows all affected users
- Requires confirmation
- Full audit trail
- Historical operation log

### Audit Log

- Comprehensive event logging
- Filter by event type and user
- Expandable event details
- Pagination support
- Export capability

## API Integration

The dashboard communicates with the FastAPI backend using the API client in `src/lib/api.ts`.

Key endpoints:
- `/api/auth/*` - Authentication
- `/api/users/*` - User management
- `/api/invites/*` - Invite operations
- `/api/admin/*` - Admin operations

## Development Tips

### Hot Module Replacement

Vite provides fast HMR out of the box. Changes to components will be reflected instantly.

### TypeScript

All types are defined in `src/types/index.ts`. Use TypeScript's type checking:

```bash
npm run build  # Will check types
```

### Styling

Uses Tailwind CSS with custom utilities defined in `src/index.css`.

### Dark Mode

Dark mode is supported using Tailwind's dark mode classes.

## Deployment

### Build

```bash
npm run build
```

### Deploy

Deploy the `dist/` directory to any static hosting service:
- Vercel
- Netlify
- AWS S3 + CloudFront
- GitHub Pages

Make sure to set the `VITE_API_BASE_URL` environment variable to your production API URL.

## Contributing

When adding new features:
1. Create new components in `src/components/`
2. Add new pages in `src/pages/`
3. Update types in `src/types/index.ts`
4. Add routes in `src/App.tsx`
5. Update this README

## License

Part of the Arborescent Trust project.
