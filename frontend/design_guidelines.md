# ML Assistant Platform Design Guidelines

## Design Approach

**Selected System**: Linear + Notion Hybrid with Stripe billing aesthetics
**Rationale**: Productivity-focused ML platform requiring exceptional data density, clear hierarchy, and professional polish for technical users.

**Core Principles**:
- Information density over visual decoration
- Scannable data tables and metrics
- Clear action hierarchy for complex workflows
- Professional, trustworthy aesthetic for billing/API features

---

## Typography System

**Font Stack**: Inter (primary), JetBrains Mono (code/technical)

**Scale**:
- Hero/Display: text-4xl to text-5xl, font-semibold
- Section Headers: text-2xl, font-semibold
- Subsections: text-lg, font-medium
- Body: text-sm to text-base, font-normal
- Captions/Metadata: text-xs, font-normal
- Code/Technical: text-sm, font-mono

**Line Height**: Use tight (leading-tight) for headers, relaxed (leading-relaxed) for body content

---

## Layout System

**Spacing Primitives**: Tailwind units of 2, 3, 4, 6, 8, 12, 16
- Component padding: p-4 to p-6
- Section spacing: gap-6 to gap-8
- Card spacing: p-4 internally, gap-3 between elements
- Tight groupings: gap-2 to gap-3

**Grid Structure**:
- Sidebar: Fixed 256px (w-64)
- Main content: flex-1 with max-w-7xl container
- Chart grid: grid-cols-1 md:grid-cols-2 xl:grid-cols-3
- Model cards: grid-cols-1 lg:grid-cols-2 xl:grid-cols-3

---

## Component Library

### Navigation & Layout

**Sidebar** (Left, Fixed):
- App logo + name at top (h-16, px-4)
- Navigation sections with subtle dividers
- Active state: subtle background fill
- Section headers: text-xs uppercase tracking-wide
- Icons: 20px (w-5 h-5) aligned left
- Bottom section: user profile + plan badge

**Header** (Top):
- Height: h-16
- Breadcrumb navigation for context
- Right: Plan indicator, usage badge, profile dropdown
- Border bottom separator

### Chat Interface

**Message Layout**:
- User messages: Right-aligned, max-w-3xl
- Assistant messages: Left-aligned, max-w-4xl
- Avatar circles: 32px (w-8 h-8)
- Message spacing: gap-4 vertically
- Timestamp: text-xs below message

**Query Type Badge**: Inline pill showing "Simple Query" or "Data-Based Query" with icon

**Input Area** (Bottom, Sticky):
- Height: auto-expanding textarea (min-h-[52px])
- File upload button (left)
- Send button (right, primary)
- Suggestion chips above input when empty

### Chart Components

**Smart Chart Container**:
- White card background
- Title: text-lg font-semibold, mb-3
- Chart area: min-h-[300px]
- Legend: Positioned right or bottom based on data
- Grid layout for multiple charts: gap-6

**Chart Types**:
- Pie charts: 300x300px, centered
- Bar charts: Full width, responsive height
- Line charts: Full width, min-h-[250px]
- Heatmap: Square aspect ratio

**Download Button**: Small, secondary style in chart header (top-right)

### Model & Dataset Cards

**Model Card**:
- Border card with hover shadow elevation
- Header: Model name (text-lg font-semibold) + version badge
- Metrics row: Accuracy, F1, Loss in compact grid (grid-cols-3)
- Metadata: text-xs with icons (dataset used, date, status)
- Action buttons: Download, API, Delete in footer (gap-2)

**Dataset Card**:
- Similar structure to model card
- Preview: First 3 rows in compact table
- Stats: Row count, column count, file size
- Status indicator: Processing/Ready/Error

### Fine-Tuning Interface

**Modal** (Large, Centered):
- Width: max-w-3xl
- Header: Title + close button
- Body: Two-column layout (config left, preview right)
- Parameter inputs: Vertical form layout with labels above
- Progress section: Linear progress bar + status text + ETA
- Footer: Cancel + Start buttons (gap-3)

**Progress Tracker**:
- Steps: Preparing → Training → Evaluating → Deploying
- Visual: Horizontal step indicator with checkmarks
- Live metrics: Loss/Accuracy updating in real-time
- Log stream: Scrollable code block (max-h-64)

### Billing & Subscription

**Plan Comparison Cards**:
- Three columns (Free, Pro, Enterprise)
- Equal height cards with border
- Header: Plan name + price (text-3xl)
- Feature list: Checkmarks with text-sm items
- CTA button at bottom (full width)
- Current plan: Highlighted with "Current" badge

**Usage Dashboard**:
- Large stat cards: Query count, Fine-tune jobs, API calls
- Grid: grid-cols-2 md:grid-cols-4, gap-4
- Progress bars showing limit usage
- Upgrade banner when near limits

### API Endpoint Display

**Code Block**:
- Full-width code display with JetBrains Mono
- Copy button (top-right)
- Syntax highlighting for endpoint URL, headers, body
- Example response collapse/expand section below

---

## Data Tables

**Structure**:
- Compact row height (h-12)
- Zebra striping for readability
- Sticky header row
- Sort indicators in headers
- Hover state on rows
- Action column (right-aligned) with icon buttons

**Pagination**: Bottom center, showing "X-Y of Z results"

---

## Interactions

**Buttons**:
- Primary: px-4 py-2, rounded-lg, font-medium
- Secondary: Similar with border
- Ghost: No background, hover state only
- Icon buttons: p-2, rounded-md
- Buttons on images: Blurred background (backdrop-blur-md)

**Modals**: Slide-in animation from center, overlay backdrop

**Notifications**: Toast-style in top-right, auto-dismiss after 5s

**Loading States**: Skeleton screens for charts/cards, spinner for buttons

---

## Images

**Not Required**: This is a data-dense productivity tool. No hero images or marketing imagery needed. Focus on functional UI with icons, charts, and data visualizations. All visual communication through typography, spacing, and component design.