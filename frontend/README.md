# Trading Journal Frontend

Production-ready Next.js frontend for trading journal and analytics platform.

## Features

- **Authentication**: Secure login/register with JWT tokens
- **Dashboard**: Overview of trading performance
- **Trade Management**: View, create, and edit trades
- **MT5 Integration**: Connect MT5 accounts and sync trades
- **Analytics**: Performance charts and metrics
- **Journal**: Detailed trade notes and tagging

## Setup

### 1. Install Dependencies

```bash
npm install
# or
yarn install
```

### 2. Configure Environment

Copy `.env.local.example` to `.env.local`:

```bash
cp .env.local.example .env.local
```

Update `NEXT_PUBLIC_API_URL` to your backend URL.

### 3. Run Development Server

```bash
npm run dev
# or
yarn dev
```

Open [http://localhost:3000](http://localhost:3000)

### 4. Build for Production

```bash
npm run build
npm start
```

## Project Structure

```
frontend/
├── src/
│   ├── components/      # Reusable React components
│   ├── contexts/        # React contexts (Auth, etc.)
│   ├── lib/            # Utilities and API client
│   ├── pages/          # Next.js pages
│   └── styles/         # Global styles
├── public/             # Static assets
├── package.json
└── tsconfig.json
```

## Pages

- `/` - Landing page
- `/login` - Login page
- `/register` - Registration page
- `/dashboard` - Main dashboard (protected)
- `/trades` - Trade list and management (protected)
- `/analytics` - Analytics and charts (protected)
- `/mt5` - MT5 account management (protected)
- `/journal` - Trade journal (protected)

## Security Features

- HttpOnly cookies for refresh tokens
- JWT access tokens
- Automatic token refresh
- Protected routes
- CORS configuration

## Technologies

- **Framework**: Next.js 14
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **HTTP Client**: Axios
- **Charts**: Recharts
- **Forms**: React Hook Form + Zod

## License

MIT
