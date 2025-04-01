# Rongai Sub-County License Management System

A Flask-based web application for managing business licenses in Rongai Sub-County, Nakuru. Designed to replace manual license tracking with a digital system.

![Demo Screenshot](screenshots/demo.png) <!-- Add your own screenshot -->

## Features

- **User Authentication**:
  - Predefined users (JOY, WILL, STAN, etc.) with secure login.
  - Admins (AGNES and STANLY) with elevated privileges.
- **License Management**:
  - Add licenses with auto-generated sequential entry numbers (resets yearly).
  - Search licenses by business name, ID, or activity.
  - Delete licenses (admin-only feature).
- **Security**:
  - Session management with secret keys.
  - Input validation for business names, phone numbers, and activities.
- **Responsive UI**:
  - Clean interface with government and county branding.
  - Live search functionality.

## Technologies Used

- **Backend**: Python, Flask, SQLite
- **Frontend**: HTML, CSS, JavaScript (AJAX for live search)
- **Database**: SQLite3
- **Tools**: Git, GitHub

## Installation

### Prerequisites

- Python 3.8+
- Git

### Steps

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/rongai-license-management.git
   cd rongai-license-management
