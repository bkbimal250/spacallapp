/** @type {import('tailwindcss').Config} */
export default {
    darkMode: "class",

    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],

    theme: {
        extend: {

            colors: {

                /* MAIN BACKGROUNDS */
                background: "#0B1120",     // main page background
                sidebar: "#111827",        // sidebar
                card: "#1F2937",           // cards
                cardHover: "#273244",

                /* PRIMARY BRAND */
                primary: {
                    DEFAULT: "#3B82F6",
                    hover: "#2563EB",
                    soft: "#1E3A8A"
                },

                /* ACCENT COLORS */
                accent: {
                    purple: "#8B5CF6",
                    cyan: "#06B6D4"
                },

                /* TEXT COLORS */
                text: {
                    primary: "#E5E7EB",
                    secondary: "#9CA3AF",
                    muted: "#6B7280"
                },

                /* BORDER */
                border: "#374151",

                /* STATUS COLORS */
                success: "#22C55E",   // incoming calls
                danger: "#EF4444",    // missed calls
                warning: "#F59E0B",   // alerts
                info: "#38BDF8",      // outgoing calls

                /* DEVICE STATUS */
                online: "#22C55E",
                offline: "#DC2626",
                idle: "#F59E0B"
            }

        },
    },

    plugins: [],
}