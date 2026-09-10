# DecisionFlow AI — Frontend

The modern web client for **DecisionFlow AI**, an enterprise Decision Operating System that transforms meeting transcripts into actionable decisions, owned action items, risk signals, and organizational momentum.

---

## Tech Stack

- **Framework**: [React 19](https://react.dev/) + [TanStack Start](https://tanstack.com/start) / [TanStack Router](https://tanstack.com/router)
- **State & Server Cache**: [TanStack React Query](https://tanstack.com/query)
- **Styling**: [Tailwind CSS](https://tailwindcss.com/)
- **Icons**: [Lucide React](https://lucide.dev/)
- **Build Tool**: [Vite](https://vitejs.dev/) + Nitro SSR

---

## Project Structure

```
Frontend/
├── public/               # Static assets & favicon
├── src/
│   ├── components/       # Reusable layout & application components
│   │   └── auth-shell.tsx
│   ├── lib/              # API client, session management, and utilities
│   │   ├── api.ts        # Type-safe API client & request wrappers
│   │   ├── session.tsx   # Authentication context & session provider
│   │   └── utils.ts      # Class merging utilities (cn)
│   ├── routes/           # File-based TanStack routes
│   │   ├── __root.tsx    # App root shell & provider wrapper
│   │   ├── index.tsx     # Landing & interactive product intro
│   │   ├── login.tsx     # Sign-in flow
│   │   ├── signup.tsx    # Organization registration flow
│   │   ├── app.tsx       # Authenticated workspace layout & sidebar
│   │   └── app/
│   │       ├── index.tsx # Overview dashboard & meeting ingestion
│   │       └── tasks.tsx # Task management & status transitions
│   ├── router.tsx        # TanStack Router instance creation
│   ├── server.ts         # Nitro server entry & SSR error boundaries
│   ├── start.ts          # Start middleware & CSRF configuration
│   └── styles.css        # Global CSS & custom design tokens
├── package.json
├── tsconfig.json
└── vite.config.ts        # Vite configuration & backend API proxy
```

---

## Getting Started

### 1. Install Dependencies
```bash
npm install
```

### 2. Development Server
```bash
npm run dev
```

The application will start on `http://localhost:5173`. API requests to `/api` are automatically proxied to the backend at `http://127.0.0.1:8000`.

### 3. Production Build
```bash
npm run build
```

### 4. Preview Production Build
```bash
npm run preview
```
