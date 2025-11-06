# KAF Art & Craft School - Enrollment System

Web-based enrollment and management system for a small art & craft school in Brisbane, Australia.

## Overview

This application uses **SurveyJS** to create forms that interface directly with **Airtable** for:
- Parent enrollment workflow
- Student management
- Class enrollment
- Attendance tracking
- Payment management

## Tech Stack

- **Frontend:** SurveyJS (form builder and renderer)
- **Backend/Database:** Airtable
- **Integration:** Airtable REST API

## Project Structure

```
KAF-Office/
├── docs/                      # Documentation
│   ├── HANDOVER.md           # Complete project context
│   ├── SCHEMA_V2.md          # Airtable database schema
│   ├── VIEWS.md              # Airtable view configurations
│   └── sample_data/          # Test data CSVs
├── scripts/                   # Python utilities
│   ├── inspect_existing_base.py
│   ├── verify_base.py
│   └── requirements.txt
├── src/                       # SurveyJS application (to be built)
├── LICENSE.txt
└── README.md                  # This file
```

## Airtable Schema

The system manages 8 interconnected tables:

1. **Households** - Family addresses
2. **Parents** - Contact information, pickup authorization
3. **Students** - Student records with medical notes
4. **Venues** - Class locations
5. **Teachers** - Instructors
6. **Classes** - Term and holiday programs
7. **Enrollments** - Student-Class junction with payment tracking
8. **Attendance** - Individual session records

See `docs/SCHEMA_V2.md` for complete field specifications.

## Getting Started

### Prerequisites

- Node.js (for SurveyJS)
- Python 3.12+ (for utility scripts)
- Airtable account with API access

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd KAF-Office
   ```

2. **Install dependencies** (when package.json is created)
   ```bash
   npm install
   ```

3. **Configure Airtable**
   - Create `.env` file with:
     ```
     AIRTABLE_API_KEY=your_api_key
     AIRTABLE_BASE_ID=appNuMdxaiSYdgxJS
     ```
   - Get API key from: https://airtable.com/create/tokens

4. **Test Airtable connection**
   ```bash
   cd scripts
   pip3 install -r requirements.txt
   export AIRTABLE_API_KEY='your_key'
   python3 inspect_existing_base.py appNuMdxaiSYdgxJS
   ```

## Documentation

- **Start Here:** `docs/HANDOVER.md` - Complete project overview and development guide
- **Schema Reference:** `docs/SCHEMA_V2.md` - Every table, field, formula, and relationship
- **Views:** `docs/VIEWS.md` - Airtable view configurations
- **Implementation Checklist:** `docs/IMPLEMENTATION_CHECKLIST.md`

## Australian-Specific Features

- **OSHC Collection** - Outside School Hours Care pickup option
- **Local Schools** - Ironside SS, St Lucia Kindergarten, etc.
- **Address Format** - Street/Suburb/Postcode (not City/State/ZIP)

## Development Roadmap

### Phase 1: Parent Enrollment
- [ ] Browse available classes
- [ ] Enroll student with full details
- [ ] Emergency contacts and photo permissions

### Phase 2: Admin Functions
- [ ] Daily attendance roll call
- [ ] Payment status management
- [ ] Student medical notes dashboard

### Phase 3: Reporting
- [ ] Enrollment statistics
- [ ] Revenue reports
- [ ] Attendance tracking

## License

See LICENSE.txt

## Contact

Anthony Lee - Project Owner

---

**Note:** This project was cleaned up on 2025-11-05. Old files are in `archive_2025-11-05/` for reference.
