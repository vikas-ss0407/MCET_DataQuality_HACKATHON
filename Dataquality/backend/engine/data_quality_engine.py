from __future__ import annotations

from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import re
from email_validator import EmailNotValidError, validate_email
from rapidfuzz import fuzz, process as rf_process

from .reference_loader import (
    load_email_domains,
    load_json_map,
    load_json_set,
)


class DataQualityEngine:
    """Offline-first data quality engine for B2B CSVs."""

    def __init__(self) -> None:
        self.countries = load_json_set("countries.json")
        self.industries = load_json_set("industries.json")
        self.job_title_map = load_json_map("job_title_map.json")
        self.email_domains = load_email_domains("email_domains.csv")

        self.accept_threshold = 0.80
        self.suggest_threshold = 0.60

        # All detected columns will be stored in the dataframe
        # No hardcoded column list; everything is dynamic

    def process_csv(self, file_bytes: bytes, data_type: str = "people") -> Dict[str, Any]:
        """Process CSV file and return cleaned data, report, and fixes."""
        df = pd.read_csv(BytesIO(file_bytes))
        return self._process_dataframe(df, data_type=data_type)

    def process_excel(self, file_bytes: bytes, data_type: str = "people") -> Dict[str, Any]:
        """Process Excel file (.xlsx or .xls) and return cleaned data, report, and fixes."""
        df = pd.read_excel(BytesIO(file_bytes))
        return self._process_dataframe(df, data_type=data_type)

    def _process_dataframe(self, df: pd.DataFrame, data_type: str = "people") -> Dict[str, Any]:
        """Core processing logic: normalize, detect issues, fix, and report."""
        df = self._normalize_columns(df)
        df = df.replace({"": np.nan, " ": np.nan})

        fixes: List[Dict[str, Any]] = []
        invalid_count = 0
        standardized_count = 0
        offline_fixes = 0
        online_fixes = 0
        manual_review = 0
        
        # Track records with issues
        missing_records = []  # Records with missing fields
        invalid_records = []  # Records with invalid formats
        duplicate_records = []  # Duplicate records

        # Get all columns from the dataframe - FULLY DYNAMIC
        all_columns = set(df.columns)

        # Apply domain derivation if needed
        if "domain" not in df.columns and ("website" in df.columns or "domain_url" in df.columns):
            df = self._derive_domain(df)

        # Detect duplicates
        duplicate_flags, duplicate_count = self._detect_duplicates(df, data_type=data_type)
        df["is_duplicate"] = duplicate_flags
        
        # Track duplicate records
        for idx, is_dup in enumerate(duplicate_flags):
            if is_dup:
                duplicate_records.append({"row_index": idx})

        # Process each row
        for idx, row in df.iterrows():
            # Apply standardization for known reference fields
            for field in ["country", "industry"]:
                if field not in df.columns:
                    continue

                if field == "country":
                    ref_set = self.countries
                elif field == "industry":
                    ref_set = self.industries
                else:
                    continue

                value, conf, mode, note = self._standardize_value(
                    str(row.get(field, "")), ref_set, field=field
                )
                if value != row.get(field):
                    standardized_count += 1
                    fixes.append(self._make_fix(idx, field, row.get(field), value, conf, mode, note))
                    if mode == "OFFLINE":
                        offline_fixes += 1
                    elif mode == "ONLINE":
                        online_fixes += 1
                    if mode == "ONLINE" and conf < self.accept_threshold:
                        manual_review += 1
                elif pd.isna(row.get(field)):
                    invalid_count += 1

            # Job title validation - check against job descriptions in cache
            if "job_title" in df.columns or "jobtitle" in df.columns:
                job_field = "job_title" if "job_title" in df.columns else "jobtitle"
                job_val = row.get(job_field, "")
                if pd.notna(job_val):
                    is_valid, mapped_title, j_conf, j_note = self._validate_job_title(str(job_val))
                    if not is_valid:
                        invalid_count += 1
                        suggestion = mapped_title or "(No match found - manual review needed)"
                        invalid_records.append({"row_index": idx, "field": job_field, "value": job_val, "issue": j_note})
                        fixes.append(self._make_fix(idx, job_field, job_val, suggestion, 0.0, "MANUAL", j_note))
                        manual_review += 1
                    elif mapped_title and mapped_title != job_val:
                        standardized_count += 1
                        fixes.append(self._make_fix(idx, job_field, job_val, mapped_title, j_conf, "OFFLINE", j_note))
                        offline_fixes += 1

            # Email validation if field exists
            if "email" in df.columns or "people_email" in df.columns:
                email_field = "email" if "email" in df.columns else "people_email"
                email_val = row.get(email_field, "")
                if pd.notna(email_val):
                    cleaned_email, e_conf, e_mode, e_note = self._validate_email(str(email_val), row)
                    if e_conf == 0.0 and e_mode == "MANUAL":
                        # Invalid email - generate suggestion and classify OFFLINE/ONLINE
                        invalid_count += 1
                        suggestion = self._suggest_email_fix(str(email_val))
                        invalid_records.append({"row_index": idx, "field": email_field, "value": email_val, "issue": e_note})
                        # Try validating the suggestion
                        try:
                            info = validate_email(suggestion, check_deliverability=False)
                            fixed = info.normalized
                            fixes.append(self._make_fix(idx, email_field, email_val, fixed, 0.85, "OFFLINE", f"Auto-fixed: {e_note}"))
                            offline_fixes += 1
                        except EmailNotValidError:
                            fixes.append(self._make_fix(idx, email_field, email_val, suggestion, 0.0, "ONLINE", f"Needs verification: {e_note}"))
                            online_fixes += 1
                            manual_review += 1
                    elif cleaned_email and cleaned_email != email_val:
                        standardized_count += 1
                        fixes.append(self._make_fix(idx, email_field, email_val, cleaned_email, e_conf, e_mode, e_note))
                        if e_mode == "OFFLINE":
                            offline_fixes += 1
                        elif e_mode == "ONLINE":
                            online_fixes += 1
                        if e_mode == "ONLINE" and e_conf < self.accept_threshold:
                            manual_review += 1
                elif pd.isna(email_val):
                    # Track missing email
                    missing_records.append({"row_index": idx, "field": email_field, "issue": "Missing"})

            # Phone validation if field exists
            if "phone" in df.columns or "people_phone" in df.columns:
                phone_field = "phone" if "phone" in df.columns else "people_phone"
                phone_val = row.get(phone_field, "")
                if pd.notna(phone_val):
                    is_valid, cleaned_phone, p_conf, p_note = self._validate_phone_strict(str(phone_val))
                    if not is_valid:
                        invalid_count += 1
                        invalid_records.append({"row_index": idx, "field": phone_field, "value": phone_val, "issue": p_note})
                        fixes.append(self._make_fix(idx, phone_field, phone_val, cleaned_phone, 0.0, "MANUAL", p_note))
                        manual_review += 1
                    elif cleaned_phone != phone_val:
                        standardized_count += 1
                        fixes.append(self._make_fix(idx, phone_field, phone_val, cleaned_phone, p_conf, "OFFLINE", p_note))
                        offline_fixes += 1
                elif pd.isna(phone_val):
                    invalid_count += 1
                    missing_records.append({"row_index": idx, "field": phone_field, "issue": "Missing"})

            # Name validation for first_name, last_name, person_name fields
            name_fields = ["first_name", "last_name", "middle_name", "person_name"]
            for name_field in name_fields:
                if name_field not in df.columns:
                    continue
                name_val = row.get(name_field, "")
                if pd.notna(name_val):
                    is_valid, cleaned_name, n_note = self._validate_name(str(name_val))
                    if not is_valid:
                        invalid_count += 1
                        suggestion = self._suggest_name_fix(str(name_val))
                        invalid_records.append({"row_index": idx, "field": name_field, "value": name_val, "issue": n_note})
                        # If suggestion is usable, mark OFFLINE; otherwise MANUAL
                        if suggestion != name_val and not suggestion.startswith("["):
                            fixes.append(self._make_fix(idx, name_field, name_val, suggestion, 0.70, "OFFLINE", f"Auto-fixed: {n_note}"))
                            offline_fixes += 1
                        else:
                            fixes.append(self._make_fix(idx, name_field, name_val, suggestion, 0.0, "MANUAL", n_note))
                            manual_review += 1

            # ID validation - must be positive integer
            if "id" in df.columns:
                id_val = row.get("id", "")
                if pd.notna(id_val):
                    is_valid, id_note = self._validate_id(str(id_val))
                    if not is_valid:
                        invalid_count += 1
                        suggestion = self._suggest_id_fix(str(id_val))
                        invalid_records.append({"row_index": idx, "field": "id", "value": id_val, "issue": id_note})
                        if suggestion != id_val and str(suggestion).isdigit():
                            fixes.append(self._make_fix(idx, "id", id_val, suggestion, 0.80, "OFFLINE", f"Auto-fixed: {id_note}"))
                            offline_fixes += 1
                        else:
                            fixes.append(self._make_fix(idx, "id", id_val, suggestion, 0.0, "MANUAL", id_note))
                            manual_review += 1

            # Email score validation - must be 0-100
            score_fields = ["email_score", "people_email_score"]
            for score_field in score_fields:
                if score_field not in df.columns:
                    continue
                score_val = row.get(score_field, "")
                if pd.notna(score_val):
                    is_valid, score_note = self._validate_score(str(score_val))
                    if not is_valid:
                        invalid_count += 1
                        invalid_records.append({"row_index": idx, "field": score_field, "value": score_val, "issue": score_note})
                        fixes.append(self._make_fix(idx, score_field, score_val, "", 0.0, "MANUAL", score_note))
                        manual_review += 1

        # Build comprehensive report with ALL columns
        report = self._build_report(df, invalid_count, standardized_count, duplicate_count, offline_fixes, online_fixes, manual_review)
        cleaned_data = df.drop(columns=["is_duplicate"], errors="ignore").to_dict(orient="records")

        return {
            "report": report,
            "cleaned_data": cleaned_data,
            "fixes": fixes,
            "missing_records": missing_records,
            "invalid_records": invalid_records,
            "duplicate_records": duplicate_records,
        }

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        col_map = {c: c.strip().lower() for c in df.columns}
        df = df.rename(columns=col_map)
        return df

    def _derive_domain(self, df: pd.DataFrame) -> pd.DataFrame:
        # Only derive domain if domain or website columns exist
        if "domain" not in df.columns and "website" not in df.columns:
            return df
            
        def extract_domain(value: Any) -> Optional[str]:
            if pd.isna(value):
                return None
            text = str(value).lower().strip()
            text = re.sub(r"https?://", "", text)
            text = text.split("/")[0]
            if not text:
                return None
            if "." not in text:
                return None
            return text

        if "domain" in df.columns and "website" in df.columns:
            df["domain"] = df.apply(
                lambda row: extract_domain(row["domain"]) or extract_domain(row["website"]), axis=1
            )
        elif "domain" in df.columns:
            df["domain"] = df["domain"].apply(extract_domain)
        elif "website" in df.columns:
            df["domain"] = df["website"].apply(extract_domain)
        return df

    def _detect_duplicates(self, df: pd.DataFrame, data_type: str = "people") -> Tuple[List[bool], int]:
        """Detect duplicates with entity-aware rules.

        Rules:
        - People mode: same email OR same phone -> duplicate; same person + same company (fuzzy) -> duplicate; same company alone allowed.
        - Company mode: treat company as the entity; same normalized company/domain -> duplicate regardless of person fields.
        """

        email_seen: set[str] = set()
        phone_seen: set[str] = set()
        person_company_seen: List[Tuple[str, str]] = []
        flags: List[bool] = []
        duplicate_count = 0

        # Precompute dynamic column fallbacks
        company_fallback = next((c for c in df.columns if "company" in c.lower()), None)

        def norm_text(val: Any) -> str:
            if pd.isna(val):
                return ""
            return str(val).lower().strip()

        def norm_phone(val: Any) -> str:
            if pd.isna(val):
                return ""
            return re.sub(r"\D", "", str(val))

        def get_company(row: pd.Series) -> str:
            for col in ["company_name", "company", "organization", "org_name", company_fallback]:
                if col and col in row:
                    val = norm_text(row.get(col, ""))
                    if val:
                        return val
            return ""

        def get_person(row: pd.Series) -> str:
            # Prefer explicit person_name; fallback to first+last
            if "person_name" in row:
                val = norm_text(row.get("person_name", ""))
                if val:
                    return val
            first = norm_text(row.get("first_name", ""))
            last = norm_text(row.get("last_name", ""))
            middle = norm_text(row.get("middle_name", ""))
            full = " ".join([p for p in [first, middle, last] if p]).strip()
            return full

        def get_email(row: pd.Series) -> str:
            for col in ["email", "people_email", "work_email", "business_email"]:
                if col in row:
                    val = norm_text(row.get(col, ""))
                    if val:
                        return val
            return ""

        def get_phone(row: pd.Series) -> str:
            for col in ["phone", "people_phone", "work_phone", "mobile"]:
                if col in row:
                    val = norm_phone(row.get(col, ""))
                    if val:
                        return val
            return ""

        for _, row in df.iterrows():
            company = get_company(row)
            person = get_person(row)
            email = get_email(row)
            phone = get_phone(row)

            is_dup = False

            if data_type == "company":
                # In company mode, duplicates are driven by company identity (name/domain) and email/phone if present
                if email and email in email_seen:
                    is_dup = True
                elif phone and phone in phone_seen:
                    is_dup = True
                elif company:
                    for _, seen_company in person_company_seen:
                        comp_score = fuzz.token_sort_ratio(company, seen_company)
                        if comp_score >= 90:
                            is_dup = True
                            break
            else:
                # People mode: email/phone dominate, then person+company pairing
                if email and email in email_seen:
                    is_dup = True
                elif phone and phone in phone_seen:
                    is_dup = True
                elif person and company:
                    for seen_person, seen_company in person_company_seen:
                        comp_score = fuzz.token_sort_ratio(company, seen_company)
                        person_score = fuzz.token_sort_ratio(person, seen_person)
                        if comp_score >= 90 and person_score >= 90:
                            is_dup = True
                            break
                # Do not mark duplicates on company-only matches; allow multiple people per company.

            if is_dup:
                duplicate_count += 1
            else:
                if email:
                    email_seen.add(email)
                if phone:
                    phone_seen.add(phone)
                if person and company:
                    person_company_seen.append((person, company))
                elif data_type == "company" and company:
                    # Track company even if no person for company-mode duplicate detection
                    person_company_seen.append(("", company))
            flags.append(is_dup)

        return flags, duplicate_count

    def _standardize_value(
        self, value: str, reference_set: set, field: str
    ) -> Tuple[str, float, str, str]:
        if not value or value.lower() == "nan":
            return value, 0.0, "OFFLINE", "missing"

        value_clean = value.strip()
        if value_clean in reference_set:
            return value_clean, 0.95, "OFFLINE", "exact reference match"

        best_match, score = self._best_match(value_clean, reference_set)
        if best_match and score >= self.suggest_threshold:
            if score >= self.accept_threshold:
                return best_match, score, "OFFLINE", f"standardized {field}"
            return best_match, score, "OFFLINE", f"suggested {field}"

        online_suggestion, online_conf = self._online_lookup(field, value_clean)
        if online_suggestion:
            return online_suggestion, online_conf, "ONLINE", f"online escalation for {field}"

        return value_clean, 0.0, "ONLINE", "Needs Manual Review"

    def _best_match(self, value: str, reference_set: set) -> Tuple[Optional[str], float]:
        if not reference_set:
            return None, 0.0
        choices = list(reference_set)
        match, score, _ = rf_process.extractOne(value, choices, scorer=fuzz.token_sort_ratio)
        return match, score / 100.0

    def _map_job_title(self, title: str) -> Tuple[str, float, str, str]:
        if not title:
            return "", 0.0, "OFFLINE", "missing"
        normalized = title.lower().strip()
        if normalized in self.job_title_map:
            return self.job_title_map[normalized], 0.9, "OFFLINE", "mapped via dictionary"

        # fuzzy substring search
        for key, role in self.job_title_map.items():
            if key in normalized:
                return role, 0.75, "OFFLINE", "substring mapping"

        online_suggestion, online_conf = self._online_lookup("job_title", title)
        if online_suggestion:
            return online_suggestion, online_conf, "ONLINE", "online escalation"
        return "", 0.0, "ONLINE", "Needs Manual Review"

    def _validate_email(self, email: str, row: pd.Series) -> Tuple[str, float, str, str]:
        if not email or str(email).strip() == "":
            derived = self._construct_email_from_name(row)
            if derived:
                return derived, 0.65, "OFFLINE", "constructed from name"
            return "", 0.0, "MANUAL", "Email missing"

        email = str(email).strip()
        
        # Check for multiple @ symbols
        if email.count("@") != 1:
            if email.count("@") == 0:
                return email, 0.0, "MANUAL", "Invalid: missing @ symbol"
            else:
                return email, 0.0, "MANUAL", f"Invalid: contains {email.count('@')} @ symbols (should be 1)"
        
        parts = email.split("@")
        local_part = parts[0]
        domain_part = parts[1]
        
        # Validate local part (before @)
        if not local_part:
            return email, 0.0, "MANUAL", "Invalid: empty local part before @"
        
        # Check for invalid characters in local part
        if re.search(r"[^a-zA-Z0-9._+-]", local_part):
            invalid_chars = re.findall(r"[^a-zA-Z0-9._+-]", local_part)
            return email, 0.0, "MANUAL", f"Invalid: local part contains invalid characters ({', '.join(set(invalid_chars))})"
        
        # Validate domain part (after @)
        if not domain_part:
            return email, 0.0, "MANUAL", "Invalid: empty domain after @"
        
        # Domain must have at least one dot
        if "." not in domain_part:
            return email, 0.0, "MANUAL", "Invalid: domain missing . (e.g., should be gmail.com not gmailcom)"
        
        # Check for invalid characters in domain
        if re.search(r"[^a-zA-Z0-9.-]", domain_part):
            invalid_chars = re.findall(r"[^a-zA-Z0-9.-]", domain_part)
            return email, 0.0, "MANUAL", f"Invalid: domain contains invalid characters ({', '.join(set(invalid_chars))})"
        
        # Check for spaces anywhere
        if " " in email:
            return email, 0.0, "MANUAL", "Invalid: contains spaces"
        
        # Domain parts validation
        domain_parts = domain_part.split(".")
        for part in domain_parts:
            if not part:
                return email, 0.0, "MANUAL", "Invalid: domain has empty part (e.g., example..com)"
            if not re.match(r"^[a-zA-Z0-9-]+$", part):
                return email, 0.0, "MANUAL", f"Invalid: domain part '{part}' contains invalid characters"

        try:
            info = validate_email(email, check_deliverability=False)
            domain = info.domain.lower()
            if self.email_domains and domain not in self.email_domains:
                suggestion = self._closest_domain(domain)
                if suggestion:
                    fixed = f"{info.local_part}@{suggestion}"
                    return fixed, 0.8, "OFFLINE", "domain standardized"
            return info.normalized, 0.9, "OFFLINE", "valid"
        except EmailNotValidError as e:
            # Check if we can derive from name
            derived = self._construct_email_from_name(row)
            if derived:
                return derived, 0.7, "OFFLINE", "reconstructed from name"
            return email, 0.0, "MANUAL", f"Invalid email format: {str(e)}"

    def _closest_domain(self, domain: str) -> Optional[str]:
        if not self.email_domains:
            return None
        match, score, _ = rf_process.extractOne(domain, list(self.email_domains), scorer=fuzz.ratio)
        return match if score >= 70 else None

    def _construct_email_from_name(self, row: pd.Series) -> Optional[str]:
        person_name = str(row.get("person_name", ""))
        domain = row.get("domain")
        if not person_name or not domain:
            return None
        parts = person_name.strip().lower().split()
        if not parts:
            return None
        local = parts[0]
        if len(parts) > 1:
            local = f"{parts[0][0]}{parts[-1]}"
        return f"{local}@{domain}"

    def _validate_phone_strict(self, phone: str) -> Tuple[bool, str, float, str]:
        """Strict phone validation: must be 10+ digits (country code optional)."""
        if not phone:
            return False, "", 0.0, "Phone number missing"
        
        # Remove all non-digit characters
        digits = re.sub(r"\D", "", phone)
        
        # Must have at least 10 digits
        if len(digits) < 10:
            return False, phone, 0.0, f"Invalid: only {len(digits)} digits (need 10+)"
        
        # Too many digits
        if len(digits) > 15:
            return False, phone, 0.0, f"Invalid: too many digits ({len(digits)})"
        
        # Valid phone - format with +
        formatted = "+" + digits
        if formatted != phone:
            return True, formatted, 0.85, "Standardized format"
        
        return True, phone, 1.0, "Valid"
    
    def _validate_name(self, name: str) -> Tuple[bool, str, str]:
        """Validate name: no special characters or numbers allowed."""
        if not name:
            return True, name, "Valid"
        
        # Check for numbers
        if re.search(r"\d", name):
            return False, name, "Invalid: contains numbers"
        
        # Check for special characters (allow spaces, hyphens, apostrophes)
        if re.search(r"[^a-zA-Z\s\-\']", name):
            invalid_chars = re.findall(r"[^a-zA-Z\s\-\']", name)
            return False, name, f"Invalid: contains special characters ({', '.join(set(invalid_chars))})"
        
        return True, name, "Valid"
    
    def _validate_id(self, id_val: str) -> Tuple[bool, str]:
        """Validate ID: must be positive integer only."""
        if not id_val or str(id_val).strip() == "":
            return False, "ID is empty"
        
        # Check if it contains only digits
        if not re.match(r"^\d+$", str(id_val).strip()):
            return False, "ID must contain only numbers"
        
        # Check if positive
        try:
            id_num = int(id_val)
            if id_num <= 0:
                return False, "ID must be positive"
        except ValueError:
            return False, "ID must be a valid number"
        
        return True, "Valid"
    
    def _validate_score(self, score_val: str) -> Tuple[bool, str]:
        """Validate email score: must be 0-100, no negative or characters."""
        if not score_val or str(score_val).strip() == "":
            return False, "Score is empty"
        
        # Check if numeric
        try:
            score = float(score_val)
            if score < 0:
                return False, "Score cannot be negative"
            if score > 100:
                return False, "Score cannot exceed 100"
        except ValueError:
            return False, "Score must be numeric"
        
        return True, "Valid"
    
    def _validate_job_title(self, job_title: str) -> Tuple[bool, Optional[str], float, str]:
        """Validate job title against job descriptions in cache."""
        if not job_title or job_title.strip() == "":
            return False, None, 0.0, "Job title is empty"
        
        job_title_clean = job_title.strip().lower()
        
        # Check if it exists in job_title_map
        if job_title_clean in self.job_title_map:
            mapped = self.job_title_map[job_title_clean]
            if mapped != job_title:
                return True, mapped, 0.9, "Standardized to known job title"
            return True, job_title, 1.0, "Valid job title"
        
        # Try fuzzy match
        if self.job_title_map:
            match, score, _ = rf_process.extractOne(
                job_title_clean, 
                list(self.job_title_map.keys()), 
                scorer=fuzz.token_sort_ratio
            )
            if score >= 85:
                mapped = self.job_title_map[match]
                return True, mapped, 0.8, f"Similar to '{match}'"
            elif score >= 70:
                return False, None, 0.0, f"Unrecognized job title (closest: '{match}' - {score}% match)"
        
        return False, None, 0.0, "Unrecognized job title"
    
    def _suggest_email_fix(self, email: str) -> str:
        email = str(email).strip()
        if email.count("@") > 1:
            parts = email.split("@")
            email = parts[0] + "@" + "".join(parts[1:])
        if "@" in email:
            local, domain = email.split("@", 1)
            domain = re.sub(r"[^a-zA-Z0-9.-]", "", domain)
            local = re.sub(r"[^a-zA-Z0-9._+-]", "", local)
            email = f"{local}@{domain}"
        if "@" in email:
            local, domain = email.split("@", 1)
            if "." not in domain and domain:
                email = f"{local}@{domain}.com"
        return email
    
    def _suggest_name_fix(self, name: str) -> str:
        # Check if name is purely numeric
        if re.match(r"^\d+$", str(name).strip()):
            return "[Name should contain characters, not numbers]"
        cleaned = re.sub(r"\d", "", str(name))
        cleaned = re.sub(r"[^a-zA-Z\s\-\']", "", cleaned)
        cleaned = " ".join(cleaned.split())
        return cleaned.strip() if cleaned.strip() else name
    
    def _suggest_id_fix(self, id_val: str) -> str:
        try:
            digits = re.sub(r"\D", "", str(id_val).strip())
            if digits:
                return digits
            id_num = int(id_val)
            return str(abs(id_num)) if id_num < 0 else str(id_num)
        except:
            return str(id_val)
    
    def _clean_phone(self, phone: str) -> str:
        """Clean and standardize phone number format."""
        if not phone:
            return ""
        # Remove all non-digit characters
        digits = re.sub(r"\D", "", phone)
        # Format as international style if valid length
        if 7 <= len(digits) <= 15:
            return "+" + digits
        return phone

    def _validate_phone(self, phone: str) -> Tuple[str, float, str, str]:
        if not phone:
            return "", 0.0, "OFFLINE", "missing"
        digits = re.sub(r"\D", "", phone)
        if 7 <= len(digits) <= 15:
            formatted = "+" + digits
            return formatted, 0.85, "OFFLINE", "normalized"

        online_suggestion, online_conf = self._online_lookup("phone", phone)
        if online_suggestion:
            return online_suggestion, online_conf, "ONLINE", "online escalation"
        return phone, 0.0, "ONLINE", "Needs Manual Review"

    def _online_lookup(self, field: str, value: str) -> Tuple[Optional[str], float]:
        # Mock external enrichment; returns slightly cleaned value
        if not value:
            return None, 0.0
        cleaned = value.strip().title()
        confidence = 0.82
        return cleaned, confidence

    def _make_fix(
        self,
        row_index: int,
        field: str,
        original: Any,
        suggested: Any,
        confidence: float,
        processing_mode: str,
        note: str,
    ) -> Dict[str, Any]:
        return {
            "row_index": int(row_index),
            "field": field,
            "original": original,
            "suggested": suggested,
            "confidence": round(confidence, 2),
            "processing_mode": processing_mode,
            "note": note,
        }

    def _build_report(
        self,
        df: pd.DataFrame,
        invalid_count: int,
        standardized_count: int,
        duplicate_count: int,
        offline_fixes: int,
        online_fixes: int,
        manual_review: int,
    ) -> Dict[str, Any]:
        """Build dynamic report showing statistics for ALL columns in the dataset."""
        # Count missing values per column
        missing_per_column = df.isnull().sum().to_dict()
        
        total_rows = df.shape[0]
        total_cols = df.shape[1]
        total_cells = total_rows * total_cols
        
        # Total missing values across all columns
        total_missing = df.isnull().sum().sum()
        
        penalty = total_missing + invalid_count + duplicate_count * 2 + manual_review * 3
        quality_score = max(0, min(100, 100 - round((penalty / (total_cells + 1)) * 100, 2)))

        return {
            "missing_fields": int(total_missing),
            "invalid_fields": invalid_count,
            "duplicate_rows": duplicate_count,
            "standardized_fields": standardized_count,
            "offline_fixes": offline_fixes,
            "online_fixes": online_fixes,
            "manual_review": manual_review,
            "overall_quality_score": quality_score,  # Return 0-100 scale
            "records": int(total_rows),
            "total_columns": int(total_cols),
            "all_columns": list(df.columns),
            "missing_per_column": missing_per_column,
        }
