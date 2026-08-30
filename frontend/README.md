# MIT CampusOS — Frontend

React frontend for MAHE MIT CampusOS: a Student Corner workspace, an AI
Copilot chat drawer grounded in real institutional documents (via the FastAPI
backend in `../backend`), Learner-ID/OTP authentication, a student community
board, faculty/parent/admin workspaces, notifications, rewards, and global
search.

## Features

- **Persistent workspace shell** — top nav with Student Corner / Campus Info
  (+ Faculty / Admin workspaces once signed in with that role), notifications,
  global search (`⌘K`), and an AI Copilot toggle that opens as a side drawer
- **Learner-ID + OTP authentication** — signup verifies a
  `<name>.mitmpl<year>@learner.manipal.edu` Learner ID by emailing (or, with no
  SMTP configured, console-logging) a 6-digit OTP; subsequent logins are
  password-based
- **AI Copilot chat** — markdown rendering, source citations with an
  inspectable detail drawer, confidence indicators, and a community handoff
  path when official documents don't have an answer
- **Student community, rewards, notifications, admin console** — see
  `src/components/` for the full set
- **Translation support** — English 🇬🇧 · Hindi 🇮🇳 · Kannada 🇮🇳
- **Responsive** — tested at 1440/1280/1024/768/390/360px

## Tech Stack

- **React 19** + **Vite 8**
- Vanilla CSS (no framework — custom design system in `src/App.css`)

## Getting Started

```bash
# Install dependencies
npm install

# Configure the backend URL (defaults to http://localhost:8000 if unset)
cp .env.example .env

# Start development server
npm run dev

# Build for production
npm run build
```

Open [http://localhost:5173](http://localhost:5173) — the FastAPI backend
(`../backend`) must be running for auth, chat, and every other API-backed
feature to work.

## Project Structure

```
src/
├── App.jsx                # Root — workspace shell, auth/session state, modal wiring
├── App.css                # Design system (tokens, components, responsive rules)
├── api.js                 # Backend API client
├── translations.js        # EN / HI / KN string tables
└── components/
    ├── Navbar.jsx              # Top nav: tabs, search, notifications, copilot, auth
    ├── AuthModal.jsx           # Learner-ID → OTP → registration / login
    ├── ChatWindow.jsx          # AI Copilot drawer (header, messages, input)
    ├── MessageBubble.jsx       # Markdown rendering, citations, action toolbar
    ├── SourceInspector.jsx     # Citation detail drawer
    ├── StudentCorner.jsx       # Default workspace: community feed, personalization
    ├── FacultyPortal.jsx / ParentHub.jsx / AdminPortal.jsx
    ├── NotificationsDrawer.jsx / NotificationToast.jsx
    ├── RewardsModal.jsx / FeedbackModal.jsx / GlobalSearchModal.jsx
    ├── AICommunityHandoffModal.jsx / ReportContentModal.jsx / TermsModal.jsx
    ├── RoleSelector.jsx / Sidebar.jsx / TypingIndicator.jsx
    └── KnowledgeLoopDiagram.jsx
```

Note: `RoleSelector.jsx` and `Sidebar.jsx` are not currently wired into
`App.jsx` (the workspace shell replaced the old role-gated single-chat layout)
— they're kept in the tree but unreachable from the running app.

## Context

Part of the *AI-Powered Institutional Intelligence Platform for MIT Manipal*
project: a RAG-grounded chatbot plus a student community/knowledge layer,
combining official institutional documents with peer-verified answers.
