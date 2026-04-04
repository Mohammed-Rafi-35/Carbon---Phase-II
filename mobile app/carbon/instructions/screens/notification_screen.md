# PRODUCTION-GRADE PROMPT  
## FLUTTER NOTIFICATION SCREEN UI (WIDGET-LEVEL EXPLANATION)

Act as an expert in **mobile application development using the Flutter framework**. Your task is to build a **complete, clean, and professional widget-level explanation** of a **Notification Screen UI**.

The output must be **highly structured, modular, and production-grade**, focusing purely on **theoretical explanation (no code)**.

---

# OBJECTIVE

- Deliver a **comprehensive widget-level breakdown** of the Notification Screen.
- Ensure alignment with **Material Design principles** using:
  - Primary
  - Secondary
  - Tertiary
  - Surface
  - Container colors
- Focus on **clean UI and strong UX**, avoiding over-engineering.
- Ensure the design is **scalable, modular, and production-ready**.

---

# OUTPUT REQUIREMENTS

- Strictly **Markdown format**
- **No code**
- Clear headings and structured sections
- Professional and implementation-focused explanation
- Must be suitable for **real-world production development**

---

# UI WIDGET REQUIREMENTS

You must **list and explain all widgets** required for a Notification Screen, including but not limited to:

### Core Layout
- Scaffold (base structure)
- AppBar (title + optional actions like mark all as read, filter)
- SafeArea (device compatibility)
- Container (surface background)

---

### Layout Structure
- Column / Row / Flex layouts (structured arrangement)
- Stack (optional for overlays like unread indicators)

---

### Content Display
- ListView / ScrollView (for notifications list)
- Cards / Containers (for each notification item)
- ExpansionTile (optional for detailed notifications)

---

### Notification Item Components
Each notification item should include:
- Title
- Description/message
- Timestamp
- Status indicator (read/unread)
- Optional icon/avatar

---

### Actions & Interaction
- IconButton (mark as read, delete, filter)
- Gesture-based interactions (tap to view details)
- Optional buttons:
  - Primary action (e.g., View Details)
  - Secondary action (e.g., Dismiss)

---

### Feedback Components
- SnackBar (for actions like delete/mark read)
- AlertDialog (for confirmations such as clear all notifications)

---

### Navigation
- BottomNavigationBar (navigation across core screens)
- AppBar navigation consistency

---

# MATERIAL THEME REQUIREMENTS

Ensure strict adherence to **centralized Material Theme usage**:

| Color Type | Usage |
|------------|------|
| Primary | Key actions, highlights, unread indicators |
| Secondary | Secondary actions (filter, dismiss) |
| Tertiary | Helper elements (timestamps, subtle UI) |
| Surface | Screen background |
| Container | Notification cards |

---

### Theme Rules

- No hardcoded colors
- All styling derived from `ColorScheme`
- Support:
  - Light mode
  - Dark mode
- Maintain consistent typography hierarchy

---

# USER EXPERIENCE (UX) REQUIREMENTS

### Core UX Principles

- Clean and minimal layout
- Easy-to-scan notification list
- Clear distinction between:
  - Read vs Unread notifications
- Fast interaction with minimal steps

---

### Notification Behavior

- Unread notifications visually highlighted
- Read notifications subdued
- Clear status indicators

---

### Error Handling

- Display errors using SnackBar
- Confirm destructive actions using AlertDialog

---

### Performance

- Efficient list rendering (lazy loading conceptually)
- Smooth scrolling experience

---

# NAVIGATION REQUIREMENTS

### Navigation Flow

- Seamless transition between:
  - Home
  - Notifications
  - Other core screens

---

### Back Button Handling

- If user is on any **core screen**:
  - Back → Navigate to **Home Screen**
- If user is on **Home Screen**:
  - Back → Show **Exit Confirmation Dialog**

---

### Navigation Rules

- Avoid screen stacking
- Use clean navigation transitions
- Maintain consistent AppBar behavior
- BottomNavigationBar must:
  - Be persistent
  - Use index-based navigation
  - Avoid route duplication

---

# SCALABILITY & FLEXIBILITY

### Modular Design

- Each component should be reusable:
  - NotificationCard
  - StatusIndicator
  - ActionButtons
  - FilterBar

---

### Centralized Control

- Theme must be globally controlled
- Navigation must be centralized
- State logic should be abstracted (conceptually)

---

### Future Extensibility

Design must support:

- Notification categorization
- Filtering (type, date, status)
- Real-time updates
- Push notification integration
- Notification grouping
- Analytics tracking

---

# STRUCTURE OF RESPONSE

Your response must include:

1. Overview
2. Complete Widget Hierarchy
3. Widget-Level Explanation
4. Notification Item Structure
5. Material Theme Integration
6. UX Design Principles
7. Navigation System
8. Feedback & Error Handling
9. Scalability & Extensibility
10. Final Summary

---

# FINAL INSTRUCTION

- Do NOT include code
- Do NOT include folder structure
- Maintain **professional tone**
- Ensure the explanation is:
  - Clear
  - Scalable
  - Implementation-ready

---
