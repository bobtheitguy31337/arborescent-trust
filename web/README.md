# Arborescent - User-Facing Web App

A beautiful, modern Twitter-like social network with built-in trust and accountability through an invite tree system.

## Features

### Core Social Features
- ✅ **Posts** - 280 character tweets with media support
- ✅ **Media Upload** - Images, videos, and GIFs (up to 4 per post)
- ✅ **Feed** - Personalized timeline with infinite scroll
- ✅ **Interactions** - Like, repost, reply threading
- ✅ **Follow System** - Follow/unfollow users
- ✅ **Notifications** - Real-time activity feed
- ✅ **Trust Badges** - Visual indicators of account health and status

### Trust System Integration
- **Seedling** 🌱 - New accounts
- **Branch** 🌿 - Growing accounts
- **Tree** 🌳 - Established accounts
- **Core Member** 🛡️ - Founding members

Trust levels are visible on every profile and post, creating social accountability.

## Tech Stack

- **React 18** with TypeScript
- **Vite** for fast development and builds
- **Tailwind CSS** for styling
- **React Router** for navigation
- **Axios** for API calls
- **Lucide React** for icons

## Getting Started

### Prerequisites
- Node.js 18+ and npm
- Backend API running on `http://localhost:8000`

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The app will be available at **http://localhost:5174**

### Build for Production

```bash
npm run build
npm run preview  # Preview production build
```

## Project Structure

```
src/
├── components/         # Reusable UI components
│   ├── Feed.tsx       # Main timeline feed
│   ├── PostCard.tsx   # Individual post display
│   ├── PostComposer.tsx  # Post creation form
│   ├── TrustBadge.tsx    # Trust level indicator
│   └── Layout.tsx     # Main app layout
├── pages/             # Route pages
│   ├── Home.tsx       # Home feed
│   ├── Login.tsx      # Login page
│   ├── Register.tsx   # Registration with invite
│   └── Notifications.tsx  # Notifications page
├── lib/               # Core utilities
│   ├── api.ts         # API client
│   └── auth.tsx       # Auth context
├── types/             # TypeScript types
│   └── index.ts       # Type definitions
├── App.tsx            # Main app component
└── main.tsx           # Entry point
```

## Key Features Explained

### Post Composer
- 280 character limit with live counter
- Drag-and-drop media upload
- Support for images, videos, and GIFs
- Up to 4 media attachments per post
- Reply threading

### Feed
- Infinite scroll pagination
- Real-time post creation
- Like, repost, reply actions
- Media previews (images and videos)
- Trust badges on every post

### Trust Badges
Visual indicators that show:
- Account status (active, flagged, suspended, banned)
- Core member status
- Account maturity level

### Notifications
- Like, repost, reply, follow events
- Unread count indicator
- Mark as read functionality
- Real-time updates

## Environment Variables

Create a `.env` file:

```env
VITE_API_BASE_URL=http://localhost:8000
```

## API Integration

The app connects to the Arborescent Trust backend API:

- **Auth**: `/api/auth/*` - Login, register, user info
- **Posts**: `/api/posts/*` - Create, read, delete posts
- **Social**: `/api/social/*` - Follow, like, notifications
- **Media**: `/api/media/*` - Upload and retrieve media files

## Development

### Hot Module Replacement
Vite provides instant HMR for fast development.

### Type Safety
Full TypeScript support with strict mode enabled.

### Code Style
- ESLint for code quality
- Prettier-compatible formatting
- Tailwind CSS utility classes

## Deployment

### Build
```bash
npm run build
```

Builds are output to `dist/` directory.

### Serve
Deploy the `dist/` folder to any static hosting:
- Vercel
- Netlify
- AWS S3 + CloudFront
- GitHub Pages

### Environment
Set `VITE_API_BASE_URL` to your production API URL.

## Future Enhancements

- [ ] User profiles with bio/banner editing
- [ ] Direct messages
- [ ] Advanced search
- [ ] Hashtags and trends
- [ ] User mentions autocomplete
- [ ] Post bookmarks
- [ ] Video/image editing
- [ ] PWA support for mobile

## Contributing

This is part of the Arborescent Trust system. See main project README for contribution guidelines.

## License

See LICENSE file in project root.

---

**Built with ❤️ for trust-based social networking**

