# FLUTTER DISRUPTIONS / EVENTS SCREEN UI  
## PRODUCTION-GRADE WIDGET-LEVEL DOCUMENTATION (NO CODE)

---

# 1. OVERVIEW

The Disruptions/Events Screen is a **real-time monitoring and visibility interface** that allows users to:

- View ongoing and past disruptions/events
- Understand impact (e.g., income disruption triggers)
- Track event status and severity
- Access detailed event information

In a parametric system, this screen plays a critical role in:

- Explaining **why claims were triggered**
- Providing **transparency of external events**
- Building **trust through visibility**

---

# 2. COMPLETE WIDGET HIERARCHY

```text
Disruptions / Events Screen
 ├── Scaffold
 │    ├── AppBar
 │    └── Body
 │         └── SafeArea
 │              └── Container (Surface)
 │                   └── Column / Scrollable Layout
 │                        ├── Header Section
 │                        │     ├── Title Text
 │                        │     └── Action Icons (Filter / Search)
 │                        │
 │                        ├── Summary Section (Optional)
 │                        │     └── Row / Cards
 │                        │           ├── Active Events
 │                        │           ├── Resolved Events
 │                        │           └── High Severity
 │                        │
 │                        ├── Events List Section
 │                        │     └── ListView / ScrollView
 │                        │           ├── Event Card
 │                        │           ├── Event Card
 │                        │           └── Event Card
 │                        │
 │                        └── Spacer / Padding
 │
 │    ├── FloatingActionButton (Optional)
 │
 └── BottomNavigationBar
````

---

# 3. WIDGET-LEVEL EXPLANATION

---

## 3.1 Scaffold (Foundation Layer)

**Role:**

* Serves as the base layout container
* Integrates:

  * AppBar
  * Body content
  * FloatingActionButton
  * BottomNavigationBar
  * Snackbar system

**UX Impact:**

* Provides consistent structure across the app
* Enables layered UI composition

---

## 3.2 AppBar (Navigation Layer)

**Components:**

* Title ("Disruptions" / "Events")
* Action buttons:

  * Filter events
  * Search events

**Role:**

* Identifies the screen context
* Enables quick filtering/search

**UX Impact:**

* Improves usability in large datasets
* Enhances navigation clarity

---

## 3.3 SafeArea (Device Compatibility Layer)

**Role:**

* Prevents overlap with:

  * Status bar
  * Notch
  * Gesture navigation areas

**UX Impact:**

* Ensures proper rendering across devices

---

## 3.4 Container (Surface Layer)

**Role:**

* Defines background using Material **surface color**
* Wraps all content

**Material Usage:**

* Uses `surface` color

**UX Impact:**

* Provides clean visual base
* Improves readability

---

## 3.5 Column / Scrollable Layout (Primary Structure)

**Role:**

* Organizes UI into sections:

  * Header
  * Summary
  * Events list

**Enhancement:**

* Wrapped in scrollable container

**UX Impact:**

* Smooth navigation
* Logical data hierarchy

---

# 4. EVENTS SCREEN SECTIONS

---

## 4.1 Header Section

### Widgets Used:

* Row
* Text
* IconButton

---

### Title Text

**Role:**

* Displays heading (e.g., "Active Disruptions")

**Material Usage:**

* Uses headline typography

---

### Action Icons

**Role:**

* Filter events by:

  * Type
  * Severity
  * Date

* Search specific events

**UX Impact:**

* Enables efficient data discovery

---

## 4.2 Summary Section (Optional)

### Widgets Used:

* Row / GridView
* Card / Container
* Text

---

### Summary Cards

**Role:**

* Provide quick insights:

  * Active events
  * Resolved events
  * High severity disruptions

**Material Usage:**

* Uses **container color**

**UX Impact:**

* Quick overview without scrolling
* Improves situational awareness

---

## 4.3 Events List Section (Core Component)

### Widgets Used:

* ListView / ScrollView
* Card / Container
* Text
* Icon
* ExpansionTile (optional)

---

## Event Card Structure

Each event is represented as a structured card.

---

### Card Header

* Event title (e.g., "Heavy Rainfall Alert")
* Status indicator (Active / Resolved)

---

### Card Body

* Description of disruption
* Date and time
* Location (optional)
* Impact summary (e.g., "High disruption")

---

### Card Footer

* Action buttons:

  * View Details
  * Share

---

### Status Representation

| Status   | UI Representation         |
| -------- | ------------------------- |
| Active   | Primary / alert color     |
| Resolved | Secondary / neutral color |
| Critical | Error / high alert color  |

---

**UX Impact:**

* Enables quick scanning of disruptions
* Provides clear event context

---

## 4.4 ExpansionTile (Detailed View)

**Role:**

* Expands event details:

  * Detailed description
  * Impact metrics
  * Related claims

**UX Impact:**

* Prevents clutter
* Allows deep inspection on demand

---

## 4.5 FloatingActionButton (Optional)

**Role:**

* Allows users to report a disruption or add an event

**Material Usage:**

* Uses **Primary Color**

**UX Impact:**

* Quick access to reporting functionality

---

## 4.6 Spacer / Padding

**Role:**

* Maintains spacing between elements

**UX Impact:**

* Improves readability
* Prevents visual clutter

---

# 5. BOTTOM NAVIGATION BAR

---

## Widgets Used:

* BottomNavigationBar
* BottomNavigationBarItem

---

## Role:

* Navigation across:

  * Home
  * Events
  * Claims
  * Payouts
  * Settings

---

## Behavior:

* Index-based switching
* No stacking of routes

**UX Impact:**

* Predictable navigation
* Persistent accessibility

---

# 6. FEEDBACK COMPONENTS

---

## 6.1 SnackBar

**Role:**

* Displays temporary messages

**Use Cases:**

* Event reporting success
* Errors

---

## 6.2 AlertDialog

**Role:**

* Confirms critical actions

**Use Cases:**

* Delete event
* Exit confirmation

---

# 7. MATERIAL THEME INTEGRATION

---

## 7.1 COLOR SYSTEM

| Color Type | Usage                              |
| ---------- | ---------------------------------- |
| Primary    | Add event, active status           |
| Secondary  | Secondary actions, resolved status |
| Tertiary   | Helper elements                    |
| Surface    | Background                         |
| Container  | Cards, grouped UI                  |

---

## 7.2 THEME PRINCIPLES

* Uses centralized `ColorScheme`
* No hardcoded values
* Supports:

  * Light mode
  * Dark mode

---

## 7.3 TYPOGRAPHY

* Headline → Titles
* Body → Descriptions
* Label → Buttons

---

# 8. USER EXPERIENCE (UX DESIGN)

---

## 8.1 CLARITY

* Card-based layout
* Clear separation of events

---

## 8.2 PERFORMANCE

* Lazy loading for lists
* Efficient UI updates

---

## 8.3 ACCESSIBILITY

* Large touch targets
* Clear status indicators
* Readable text

---

## 8.4 REAL-TIME VISIBILITY

* Events should update dynamically
* Reflect backend-triggered disruptions

---

# 9. NAVIGATION SYSTEM

---

## 9.1 EVENTS FLOW

```text id="events_flow"
Dashboard → Events → Event Details → Related Claims
```

---

## 9.2 BACK BUTTON HANDLING

---

### Case 1: Inside App

* Back → Navigate to Home Screen

---

### Case 2: On Home Screen

* Back → Show exit confirmation dialog

---

## 9.3 PREVENT STACKING

* Use replacement navigation
* Avoid duplicate screens

---

## 9.4 APPBAR NAVIGATION

* Provides filter/search
* Maintains consistency

---

# 10. SCALABILITY & FLEXIBILITY

---

## 10.1 MODULAR WIDGETS

Reusable components:

* EventCard
* StatusBadge
* FilterBar
* ActionButtons

---

## 10.2 CENTRALIZED THEME

* Single source for colors and typography

---

## 10.3 FUTURE EXTENSIONS

* Event categorization
* Advanced filtering
* Notifications
* Analytics dashboard
* Geo-based event mapping

---

## 10.4 MICROSERVICE ALIGNMENT

Integrates with:

* Trigger Service
* Event Bus
* Claims Service
* Analytics Service

---

# 11. FINAL SUMMARY

The Disruptions/Events Screen is designed as:

* A real-time monitoring interface
* A transparency layer for system-triggered events
* A scalable and modular UI component

It ensures:

* Clear event visualization
* Strong UX clarity
* Material Design consistency
* Alignment with backend automation

This makes it suitable for:

* Event-driven applications
* Parametric insurance systems
* Real-time analytics platforms

---
