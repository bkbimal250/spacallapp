# Frontend Architecture & Implementation Guide

This document outlines the structural design, data flow, and backend integration patterns used in the CallLog System frontend.

## 📁 Source Directory Structure (`frontend/src`)

The project follows a **Feature-Based Module Architecture**, which promotes scalability and separation of concerns.

-   **`app/`**: Core configuration and global providers.
    -   `config.js`: Environment variables and global constants.
    -   `providers.jsx`: Context providers (Auth, Redux, Query).
-   **`assets/`**: Static files like images, icons, and global CSS.
-   **`layouts/`**: Wrappers for different parts of the app.
    -   `DashboardLayout.jsx`: The primary shell with Navbar and Sidebar.
    -   `AuthLayout.jsx`: Simple shell for Login/Registration pages.
-   **`modules/`**: The heart of the application logic. Each feature (e.g., `calllogs`, `branches`, `analytics`) has its own subdirectory:
    -   `api.js`: Axios service definitions for that specific module.
    -   `components/`: UI components exclusive to the module.
    -   `pages/`: Full-page components rendered by the router.
-   **`shared/`**: Common code used across multiple modules.
    -   `components/`: Reusable UI elements (Buttons, Tables, Modals).
    -   `hooks/`: Custom React hooks (e.g., `useAuth`, `useLocalStorage`).
    -   `services/`: Global services like the `axiosInstance`.
    -   `utils/`: Helper functions (formatting, validation).
-   **`store/`**: Global state management.
    -   `index.js`: Main Redux store configuration.
    -   `slices/`: Redux Toolkit slices (Auth, Branch, Device).

---

## ⚡ Data Flow & Backend Connection

### 📡 Axios & API Layer (`shared/services/axiosInstance.js`)
Backend connectivity is centralized through a pre-configured Axios instance:
1.  **Base Configuration**: Uses `VITE_API_BASE_URL` from environment variables.
2.  **Request Interceptors**: Automatically attaches the JWT `Bearer` token to every outgoing request.
3.  **Response Interceptors**: Monitors 401 (Unauthorized) errors. If a token expires, it silently attempts to refresh it using standard `SimpleJWT` routes before retrying the original request.

### 🧠 Redux State Management (`store/`)
We use **Redux Toolkit** for predictable, global state:
-   **Auth Slice**: Manages user session, permissions (SuperAdmin vs Admin), and profile data.
-   **Resource Slices**: (Branch, Device) Caches high-frequency lookup data to reduce repetitive API calls.

### 🎣 Custom Hooks
-   **`useAuth`**: Abstracts login/logout logic and permission checks (`isSuperAdmin`).
-   **`useEffect` + `useState`**: Used within pages for local data fetching and UI state (loading, filtering).

---

## 🛠️ Key Implementation Patterns

### 1. The Filter Engine
The `CallLogList.jsx` and `AnalyticsDashboard.jsx` use a unified pattern for data fetching:
-   Filters are stored in a local `filters` state.
-   A `useEffect` hook triggers a fresh API call whenever the filters change.
-   API calls are consolidated in the module-specific `api.js` file for clean separation.

### 2. Shared Table Component
The `shared/components/Table.jsx` is a highly generic component that supports:
-   **Custom Rendering**: Pass a `render` function in columns for icons or badges.
-   **Selection Handling**: Built-in support for checkboxes and "Select All" functionality (used in Bulk Delete).

### 3. Responsive Styling
Styles are built using **Tailwind CSS**, focusing on:
-   **Mobile-First Design**: Grid layouts specifically optimized for mobile and desktop.
-   **Aesthetic Consistency**: Using a unified color palette (Sky Blue for primary actions, Red for alerts).

---

## 🚀 Adding a New Feature
To add a new module (e.g., "Settings"):
1.  Create `src/modules/settings/`.
2.  Define endpoints in `api.js`.
3.  Create page components in `pages/`.
4.  Register the routes in `src/routes/`.
5.  Add a NavLink in `src/layouts/components/Sidebar.jsx`.
