# 📊 Data Quality Guardian - QA Platform

**Theme: Data Quality & Validation Platform**  
**MCET Data Quality Hackathon 2025**

[![GitHub](https://img.shields.io/badge/GitHub-vikas--ss0407-blue?logo=github)](https://github.com/vikas-ss0407/MCET_DataQuality_HACKATHON.git)

---

## 📌 Project Overview

**Data Quality Guardian** is an intelligent, offline-first data validation and quality assurance platform designed for B2B datasets. It combines advanced fuzzy matching, reference data standardization, and AI-powered suggestions to automatically cleanse, validate, and fix data quality issues in CSV and Excel files. The platform provides transparent reporting with configurable processing modes (people vs. company data) and enables data teams to maintain enterprise-grade data integrity with minimal manual effort.

### **Problem Statement**

Business data quality challenges include:
- Inconsistent company names, contact information across records
- Duplicate entries with slight variations in names/emails
- Missing or invalid email addresses and phone numbers
- Non-standardized job titles and industry classifications
- Manual verification of problematic records consuming hours
- No transparent audit trail of corrections applied

**Our Solution:** Fully automated offline validation pipeline with AI-enhanced suggestions, entity-aware duplicate detection, and transparent reporting for data governance and compliance.

---

## 🏗️ Technical Architecture

### System Architecture Diagram

```
┌──────────────────────────────────────────────────────────┐
│              FRONTEND (React 18 + Vite)                  │
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Hero Section                                    │   │
│  │ • Data Type Toggle (People / Company Mode)      │   │
│  └─────────────────────────────────────────────────┘   │
│         ↓                                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Upload Form  │→ │   Report     │→ │  Fix Mode    │  │
│  │ (CSV/Excel)  │  │   Summary    │  │   Badges    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│         ↓              ↓                    ↓            │
│  [Progress Bar]   [7 KPIs Display]   [OFFLINE/ONLINE]   │
│         ↓              ↓                    ↓            │
│  [Download Options]                 [Verify/AI Suggest] │
│  • Cleaned CSV                                           │
│  • Excel Report (Multi-sheet)                            │
└──────────────────────────────────────────────────────────┘
                        │ Axios REST API
                        ↓
┌──────────────────────────────────────────────────────────┐
│           BACKEND (FastAPI + Python 3.10+)              │
│                                                          │
│  [POST /upload] → Orchestration Pipeline               │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  Normalize   │→ │  Validate    │→ │  Standardize│ │
│  │  Columns     │  │  Fields      │  │  Reference  │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│         ↓              ↓                     ↓          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Duplicate  │→ │ Job Title    │→ │   Report    │ │
│  │   Detection  │  │   Mapping    │  │  Generation │ │
│  │ (Entity-Aware)│  │ (ML Cache)   │  │  (7 KPIs)   │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│         ↓              ↓                                │
│  pandas/numpy   rapidfuzz.fuzz            openpyxl     │
│  email-validator  reference_loader        Jinja2       │
└──────────────────────────────────────────────────────────┘
                        │
         ┌──────────────┼──────────────┐
         ↓              ↓              ↓
    ┌────────────┐  ┌────────┐  ┌────────────┐
    │ Reference  │  │Online  │  │ Job Title  │
    │Data (JSON) │  │APIs    │  │ Map Cache  │
    │ Countries  │  │Nominat │  │(Trained ML)│
    │Industries  │  │im/etc  │  │            │
    │Email Domain│  │        │  │            │
    └────────────┘  └────────┘  └────────────┘
```

### Data Processing Pipeline

```
CSV/Excel Input
     ↓
[Column Normalization] → lowercase, strip whitespace
     ↓
[Reference Loading] → Countries, Industries, Email Domains, Job Titles
     ↓
[Duplicate Detection] ⤵️
  • People Mode: Email/Phone signature + Person+Company pairing
  • Company Mode: Company identity + Email/Phone validation
     ↓
[Field Validation]
  • Email: Format check + domain validation
  • Phone: Strict format (E.164)
  • Names: Character set validation
  • Job Title: Fuzzy match against trained dictionary
  • Country/Industry: Reference data matching
     ↓
[Standardization & Fixing]
  • Offline Fixes: Reference match (confidence ≥ 80%)
  • Online Escalation: External API verification
  • Manual Review: Complex cases requiring human decision
     ↓
[Report Generation] → 7 KPIs, fixes ledger, cleaned data
     ↓
CSV/Excel Output + Download Options
```

---

## 🎯 Key Features

### 1. **Intelligent Data Validation**
- ✅ Email format and domain validation
- ✅ Phone number E.164 format enforcement
- ✅ Name character set validation
- ✅ Country/Industry reference standardization
- ✅ Job title fuzzy matching with trained ML dictionary

### 2. **Entity-Aware Duplicate Detection**
- **People Mode**: Flags same email/phone; same person + company pairing
- **Company Mode**: Identifies company duplicates by normalized name/domain
- **Smart Logic**: Different people at same company NOT flagged as duplicates

### 3. **Transparent Fix Tracking**
- Offline Fixes: Automatic corrections with confidence scores
- Online Fixes: External API verification with audit trail
- Manual Review: Complex cases highlighted for human decision
- Complete ledger of all changes with source and confidence

### 4. **Multi-Sheet Export**
- Cleaned Data: Validated and standardized records
- Missing Fields: Records with incomplete data
- Invalid Records: Format violations requiring review
- Duplicate Summary: All detected duplicates with reasoning

### 5. **Offline-First Architecture**
- Full CSV/Excel processing without internet requirement
- Local reference data caches (countries, industries, job titles)
- Optional online verification for enhanced confidence
- Privacy-first: Data never leaves your infrastructure

---

## 💻 Technology Stack

### **Frontend**
- **Framework**: React 18.2.0
- **Build Tool**: Vite 5.0+
- **Styling**: Tailwind CSS 3.3+
- **HTTP Client**: Axios 1.6+
- **UI Components**: Custom components with Tailwind

### **Backend**
- **Framework**: FastAPI 0.104+
- **Language**: Python 3.10+
- **Data Processing**: pandas 2.0+, numpy 1.24+
- **Fuzzy Matching**: rapidfuzz 3.0+
- **Email Validation**: email-validator 2.0+
- **Excel Support**: openpyxl 3.10+
- **Async**: asyncio, uvicorn

### **Reference Data & ML**
- Job Title Mapping: Trained on industry standard roles
- Country Reference: ISO 3166-1 country list
- Industry Standards: NAICS/SIC classification
- Email Domains: Public domain list for validation

### **DevOps**
- **Backend Server**: uvicorn
- **Frontend Dev**: npm / pnpm
- **API Documentation**: FastAPI auto-generated Swagger
- **CORS**: FastAPI middleware for cross-origin requests

---

## 🚀 Getting Started

### Prerequisites
- Node.js 16+ (Frontend)
- Python 3.10+ (Backend)
- pip / venv (Python package management)
- npm / pnpm (Frontend package management)

### Installation

#### 1. **Backend Setup**
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

#### 2. **Frontend Setup**
```bash
cd frontend
npm install
# or
pnpm install
```

### Running the Application

#### **Start Backend (Terminal 1)**
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
Backend available at: `http://localhost:8000`  
API Docs: `http://localhost:8000/docs`

#### **Start Frontend (Terminal 2)**
```bash
cd frontend
npm run dev
# or
pnpm dev
```
Frontend available at: `http://localhost:5173`

---

## 📊 API Endpoints

### **POST /upload**
Upload CSV or Excel file for data quality analysis.

**Request:**
```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@data.csv" \
  -F "data_type=people"
```

**Parameters:**
- `file` (multipart/form-data): CSV or Excel file
- `data_type` (form): "people" or "company" (default: "people")

**Response:**
```json
{
  "cleaned_data": [...],
  "report": {
    "total_records": 100,
    "duplicate_count": 5,
    "invalid_count": 8,
    "standardized_count": 12,
    "offline_fixes": 10,
    "online_fixes": 2,
    "manual_review": 0
  },
  "fixes": [...]
}
```

### **GET /download/cleaned**
Download cleaned CSV file.

### **GET /download/excel**
Download comprehensive Excel report (multi-sheet).

### **POST /ai-suggest**
Get AI-powered suggestions for field values.

**Request:**
```json
{
  "field_type": "job_title",
  "value": "CEO"
}
```

### **POST /verify-online**
Online verification for email/phone fields.

---

## 📈 Report Metrics (7 KPIs)

1. **Total Records**: Input dataset size
2. **Duplicates Found**: Entity-aware duplicate count
3. **Invalid Records**: Format violations
4. **Standardized**: Fields corrected via reference matching
5. **Offline Fixes**: Auto-corrected (high confidence)
6. **Online Verification**: External API escalations
7. **Manual Review**: Cases requiring human decision

---

## 🛠️ Configuration

### Reference Data Caches
Located in `backend/cache/`:
- `countries.json` - ISO country list
- `industries.json` - Industry classifications
- `email_domains.csv` - Public email domain list
- `job_title_map.json` - ML-trained job title mappings

### Engine Thresholds
Edit in `backend/engine/data_quality_engine.py`:
```python
self.accept_threshold = 0.80    # Auto-accept confidence
self.suggest_threshold = 0.60   # Suggest if above this
```

---

## 📝 Usage Examples

### Example 1: People Data Upload
```bash
# Upload people CSV with data_type=people
curl -X POST "http://localhost:8000/upload" \
  -F "file=@contacts.csv" \
  -F "data_type=people"
```

### Example 2: Company Data Upload
```bash
# Upload company CSV with data_type=company
# Multiple people at same company NOT flagged as duplicates
curl -X POST "http://localhost:8000/upload" \
  -F "file=@companies.csv" \
  -F "data_type=company"
```

### Example 3: Download Report
```bash
# Get Excel report with all sheets
curl -X GET "http://localhost:8000/download/excel" \
  -o data_quality_report.xlsx
```

---

## 🎨 UI Components

### **App.jsx** - Main Application
- Upload form with file drop zone
- Data type toggle (People/Company)
- Report summary display
- Download options (CSV/Excel)

### **UploadForm.jsx** - File Upload Component
- Drag-and-drop support
- File validation
- Progress tracking
- Error handling

### **ReportSummary.jsx** - Metrics Display
- 7 KPI cards
- Color-coded status (pass/warning/error)
- Quick statistics

### **FixModeBadges.jsx** - Fix Type Indicators
- OFFLINE: Auto-corrected
- ONLINE: Verified externally
- MANUAL: Needs review

---

## 🔍 Duplicate Detection Logic

### **People Mode**
```
Email match → Duplicate ✓
Phone match → Duplicate ✓
Same person + Same company (fuzzy) → Duplicate ✓
Same company only → NOT duplicate (allow multiple people)
```

### **Company Mode**
```
Email match → Duplicate ✓
Phone match → Duplicate ✓
Company name match (fuzzy) → Duplicate ✓
(Different people at same company allowed)
```

---

## 📊 Sample Input/Output

### Input CSV
```
id,company_name,first_name,last_name,email,phone,job_title,country,industry
1,Acme Corp,John,Doe,john@acme.com,+1-555-0001,CEO,USA,Technology
2,ACME CORP,Jane,Smith,jane@acme.com,+1-555-0002,Manager,USA,Technology
3,Acme,John,Doe,john@acme.com,555-0001,Chief Executive Officer,US,Tech
```

### Output Report (JSON)
```json
{
  "total_records": 3,
  "duplicates": 1,
  "invalid": 0,
  "standardized": 2,
  "fixes": [
    {
      "row": 2,
      "field": "company_name",
      "original": "ACME CORP",
      "suggested": "Acme Corp",
      "confidence": 0.95,
      "mode": "OFFLINE",
      "note": "standardized company"
    },
    {
      "row": 3,
      "field": "job_title",
      "original": "Chief Executive Officer",
      "suggested": "CEO",
      "confidence": 0.90,
      "mode": "OFFLINE",
      "note": "mapped via dictionary"
    }
  ]
}
```

---

## 🧪 Testing

### Manual Testing
1. Upload sample CSV with known duplicates
2. Verify duplicate detection by data_type
3. Check offline fix application
4. Download and validate cleaned data
5. Review multi-sheet Excel report

### Test Files
Sample data files available in `sample_data.csv`

---

## 📚 Project Structure

```
Dataquality/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── requirements.txt         # Python dependencies
│   ├── engine/
│   │   ├── data_quality_engine.py  # Core validation logic
│   │   └── reference_loader.py     # Reference data loading
│   └── cache/
│       ├── countries.json
│       ├── industries.json
│       ├── email_domains.csv
│       └── job_title_map.json
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   ├── styles.css
│   │   └── components/
│   │       ├── UploadForm.jsx
│   │       ├── ReportSummary.jsx
│   │       └── FixModeBadges.jsx
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── postcss.config.js
├── sample_data.csv
└── README.md
```

---

## 🚀 Deployment

### Docker Setup (Coming Soon)
- Backend containerization
- Frontend build optimization
- Docker Compose orchestration

### Production Considerations
- Environment-based configuration
- Reference data versioning
- API rate limiting
- Request logging and monitoring
- Error tracking (Sentry integration)

---

## 🤝 Contributing

We welcome contributions! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 👥 Team

**Team Members**
- Vipin Karthik (Team Lead)
- Vikas
- Sakthivel
- Sandhya
- Sivavashini

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

- **MCET** for hosting the Data Quality Hackathon 2025
- **FastAPI** for the excellent async web framework
- **React & Vite** for modern frontend tooling
- **rapidfuzz** for accurate fuzzy matching
- **pandas** for powerful data manipulation
- Open source community for amazing libraries

---

## 📧 Contact & Support

**GitHub Repository:** https://github.com/vikas-ss0407/MCET_DataQuality_HACKATHON.git

**Issues & Feature Requests:** Please open an issue on GitHub  
**Questions?** Reach out via GitHub Discussions

---

## 🎯 Roadmap

### Phase 1 (Current)
- ✅ CSV/Excel upload and validation
- ✅ Entity-aware duplicate detection
- ✅ Offline-first processing
- ✅ Multi-sheet export

### Phase 2 (Upcoming)
- 🔄 Advanced ML-based field matching
- 🔄 Batch processing for large datasets
- 🔄 API rate limiting and authentication
- 🔄 Database integration for historical tracking

### Phase 3 (Future)
- 🔮 Real-time data streaming validation
- 🔮 Custom validation rules builder
- 🔮 Data lineage and audit trails
- 🔮 Enterprise SLA monitoring

---

**Made with ❤️ by VibeCoders Team | MCET Hackathon 2025**
