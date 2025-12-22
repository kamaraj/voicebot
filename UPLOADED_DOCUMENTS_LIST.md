# Uploaded Documents Summary
**Generated:** 2025-12-10 16:55:02

## Overview
- **Total Document Sources:** 10
- **Total Chunks in Knowledge Base:** 107

---

## Documents List

### 1. **1_System_Usage_FAQ.pdf**
- **Type:** PDF
- **Chunks:** 8
- **Topics:** System login, child enrollment, attendance tracking, mobile access, announcements, data security, support resources
- **Preview:** Childcare Center Management System user guide covering system usage FAQs

---

### 2. **2_Admission_Enrollment_FAQ.pdf**
- **Type:** PDF
- **Chunks:** 10
- **Topics:** Admission process, age groups, required documents, waitlist, enrollment options, parent visits, special needs support, toilet training policy
- **Preview:** Childcare Center admission & enrollment FAQs with comprehensive information

---

### 3. **3_Fees_Payment_FAQ.pdf**
- **Type:** PDF
- **Chunks:** 12
- **Topics:** Tuition rates, payment methods, due dates, late fees, sibling discounts, financial assistance, additional fees, refund policies, tax documentation
- **Preview:** Childcare Center fees & payment FAQs covering all financial aspects

---

### 4. **4_Hours_Schedule_FAQ.pdf**
- **Type:** PDF
- **Chunks:** 9
- **Topics:** Operating hours, drop-off/pick-up times, late pick-up policy, schedule changes, daily routines, weather closures, visiting hours
- **Preview:** Childcare Center hours & schedule FAQs with detailed timing information

---

### 5. **5_Safety_Security_FAQ.pdf**
- **Type:** PDF
- **Chunks:** 10
- **Topics:** Child safety measures, check-in/out procedures, emergency protocols, staff training, allergy management, illness policies, custody issues, background checks
- **Preview:** Childcare Center safety & security FAQs addressing parent concerns

---

### 6. **6_Food_Nutrition_FAQ (1).pdf**
- **Type:** PDF
- **Chunks:** 12
- **Topics:** Meals and snacks, dietary restrictions, sample menus, picky eaters, food allergies, bringing food from home, infant feeding, organic food, nutrition education
- **Preview:** Childcare Center food & nutrition FAQs covering all meal-related questions

---

### 7. **6_Food_Nutrition_FAQ.pdf**
- **Type:** PDF
- **Chunks:** 12
- **Topics:** Same as above (duplicate upload)
- **Preview:** Childcare Center food & nutrition FAQs (duplicate entry)

---

### 8. **7_Health_Wellness_FAQ.pdf**
- **Type:** PDF
- **Chunks:** 12
- **Topics:** Illness policy, medication administration, immunizations, injury procedures, health screenings, chronic conditions, COVID-19 protocols, special dietary needs, mental health support, cleaning protocols
- **Preview:** Childcare Center health & wellness FAQs with comprehensive health information

---

### 9. **8_Daily_Activities_FAQ.pdf**
- **Type:** PDF
- **Chunks:** 12
- **Topics:** Daily schedules, curriculum, outdoor play, special activities, literacy/math learning, rest time, field trips, screen time policy, cultural celebrations, toys from home
- **Preview:** Childcare Center daily activities FAQs covering curriculum and activities

---

### 10. **sample_knowledge** (Built-in)
- **Type:** Built-in system knowledge
- **Chunks:** 10
- **Topics:** Python programming, Machine Learning, TinyLlama model, FastAPI, Async programming, RAG (Retrieval Augmented Generation), Vector databases, AI Guardrails, ChromaDB, Voice assistants
- **Preview:** Default knowledge base with technical AI/ML topics

---

## Summary Statistics

| Category | Count |
|----------|-------|
| Total PDF Documents | 9 |
| Duplicate Documents | 1 (6_Food_Nutrition_FAQ.pdf appears twice) |
| Built-in Knowledge | 1 source (10 chunks) |
| Total Text Chunks | 107 |
| Average Chunks per Document | ~10.7 |

---

## API Endpoints Available

You can manage documents using these API endpoints:

1. **List Documents:** `GET http://localhost:9011/api/v1/documents/list`
2. **Upload Document:** `POST http://localhost:9011/api/v1/documents/upload`
3. **Upload Multiple:** `POST http://localhost:9011/api/v1/documents/upload-multiple`
4. **Search Knowledge Base:** `POST http://localhost:9011/api/v1/documents/search`
5. **Get Stats:** `GET http://localhost:9011/api/v1/documents/stats`
6. **Clear All (Caution!):** `DELETE http://localhost:9011/api/v1/documents/clear`

---

## Web Interface

Access the upload interface at:
**http://localhost:9011/static/upload_documents.html**

---

*This document is auto-generated based on the current state of the ChromaDB knowledge base.*
