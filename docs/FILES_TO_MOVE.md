# Files to Move to Flutter Project - Quick Reference

## Create New Flutter Project First
```bash
cd ~/Projects
flutter create kaf_office_web
cd kaf_office_web
```

## Then Copy These Files

### 1. Documentation → `docs/`
```bash
mkdir -p docs
cp ../KAF-Office/HANDOVER.md docs/
cp ../KAF-Office/SCHEMA_V2.md docs/
cp ../KAF-Office/VIEWS.md docs/
cp ../KAF-Office/IMPLEMENTATION_CHECKLIST.md docs/
cp ../KAF-Office/START_HERE.md docs/
cp ../KAF-Office/QUICKSTART.md docs/
cp ../KAF-Office/TODO.md docs/
cp ../KAF-Office/CLEANUP_PLAN.md docs/
```

### 2. Sample Data → `docs/sample_data/`
```bash
cp -r ../KAF-Office/sample_data docs/
```

### 3. Python Scripts → `scripts/`
```bash
mkdir -p scripts
cp ../KAF-Office/inspect_actual.py scripts/
cp ../KAF-Office/inspect_existing_base.py scripts/
cp ../KAF-Office/verify_base.py scripts/
cp ../KAF-Office/requirements.txt scripts/
```

### 4. Optional Reference → `docs/reference/`
```bash
mkdir -p docs/reference
cp ../KAF-Office/CUSTOM_APPS_PLAN.md docs/reference/
```

## Files to SKIP (Don't Move)
- `node_modules/` - Old Node.js dependencies
- `package.json`, `package-lock.json` - Old npm config
- `webpack.*.js` - Old build configs
- `css/`, `js/`, `img/` - Old web assets
- `index.html`, `404.html` - Old HTML files
- `favicon.ico`, `icon.*`, `site.webmanifest`, `robots.txt` - Old web assets
- `.editorconfig`, `.gitattributes` - Will recreate for Flutter
- `archive_2025-11-05/` - Can delete after verifying Flutter app works
- `.claude/`, `.idea/` - IDE specific, don't move

## Result Directory Structure
```
kaf_office_web/
├── lib/                          # Flutter app code (to be created)
│   ├── main.dart
│   ├── models/
│   ├── services/
│   │   └── airtable_service.dart
│   ├── screens/
│   └── widgets/
├── web/                          # Flutter web assets
├── test/                         # Tests
├── docs/                         # 📁 Moved documentation
│   ├── HANDOVER.md              # 👈 START HERE!
│   ├── SCHEMA_V2.md
│   ├── VIEWS.md
│   ├── IMPLEMENTATION_CHECKLIST.md
│   ├── START_HERE.md
│   ├── QUICKSTART.md
│   ├── TODO.md
│   ├── CLEANUP_PLAN.md
│   ├── sample_data/
│   └── reference/
│       └── CUSTOM_APPS_PLAN.md
├── scripts/                      # 📁 Python utilities
│   ├── inspect_actual.py
│   ├── inspect_existing_base.py
│   ├── verify_base.py
│   └── requirements.txt
├── .env                          # Create this! (add to .gitignore)
├── .gitignore                    # Update to include .env
├── pubspec.yaml                  # Flutter dependencies
└── README.md                     # Create new Flutter project README
```

## After Moving Files

### 1. Create `.env` File
```bash
cat > .env << 'EOF'
AIRTABLE_API_KEY=patYJhlgK2q6sAnyZ.8c3945853082593f6ec6cc6d12a0cd863a13a912a067dfd99c75a0ff95ae4e06
AIRTABLE_BASE_ID=appNuMdxaiSYdgxJS
EOF
```

### 2. Update `.gitignore`
Add these lines:
```
.env
*.env
scripts/*.pyc
```

### 3. Remove API Key from `scripts/inspect_actual.py`
Edit line 6 to use environment variable:
```python
API_KEY = os.getenv('AIRTABLE_API_KEY')
```

### 4. Install Python Dependencies (for scripts)
```bash
cd scripts
pip3 install -r requirements.txt
cd ..
```

### 5. Test Airtable Connection
```bash
cd scripts
python3 inspect_actual.py
cd ..
```

### 6. Read HANDOVER.md
Open `docs/HANDOVER.md` - it has everything you need to know!

## Quick Start Command Chain
```bash
# Create Flutter project
cd ~/Projects
flutter create kaf_office_web
cd kaf_office_web

# Copy files
mkdir -p docs scripts docs/reference
cp ../KAF-Office/HANDOVER.md docs/
cp ../KAF-Office/SCHEMA_V2.md docs/
cp ../KAF-Office/VIEWS.md docs/
cp ../KAF-Office/IMPLEMENTATION_CHECKLIST.md docs/
cp ../KAF-Office/START_HERE.md docs/
cp ../KAF-Office/QUICKSTART.md docs/
cp ../KAF-Office/TODO.md docs/
cp ../KAF-Office/CLEANUP_PLAN.md docs/
cp -r ../KAF-Office/sample_data docs/
cp ../KAF-Office/CUSTOM_APPS_PLAN.md docs/reference/
cp ../KAF-Office/inspect_actual.py scripts/
cp ../KAF-Office/inspect_existing_base.py scripts/
cp ../KAF-Office/verify_base.py scripts/
cp ../KAF-Office/requirements.txt scripts/

# Create .env
echo "AIRTABLE_API_KEY=patYJhlgK2q6sAnyZ.8c3945853082593f6ec6cc6d12a0cd863a13a912a067dfd99c75a0ff95ae4e06" > .env
echo "AIRTABLE_BASE_ID=appNuMdxaiSYdgxJS" >> .env

# Update .gitignore
echo ".env" >> .gitignore
echo "*.env" >> .gitignore

# You're ready! Read docs/HANDOVER.md next
```

---

**Next:** Read `docs/HANDOVER.md` for full project context and Flutter development guide.
