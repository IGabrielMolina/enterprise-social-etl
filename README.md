# Enterprise Multi-Platform ETL Pipeline

![n8n](https://img.shields.io/badge/Orchestrator-n8n-FF6560?style=for-the-badge&logo=n8n&logoColor=white)
![Postgres](https://img.shields.io/badge/Database-PostgreSQL-336791?style=for-the-badge&logo=postgresql&logoColor=white)
![JavaScript](https://img.shields.io/badge/Scripting-JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![Docker](https://img.shields.io/badge/Deployment-Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

> **High-availability orchestration system managing data synchronization across 23 corporate social media accounts (TikTok, Meta, YouTube).**

## Project Overview

This repository documents the logic structure of a production-grade ETL (Extract, Transform, Load) pipeline designed to handle social metrics datasets without downtime.

The system serves as the integration layer between raw API data, manual Excel reporting, and a centralized Data Warehouse.

### Key Metrics

- **Scale:** Manages data for 23 distinct brand accounts.
- **Volume:** Processes daily engagement metrics via batched execution.
- **Reliability:** Implements automated token rotation and proactive rate-limiting logic.

---

## System Architecture

The following diagram illustrates the routing logic required to handle multiple data sources, specific platform quirks (e.g., Instagram vs. Facebook structures), and database upsert strategies.

![System Visual Map](/visual_map.png)
_(High-level orchestration view showing branching logic)_

---

## Workflow Modules

### 1. Self-Healing Authentication (Token Rotation)

_(See `/0-token-refresh`)_
![Token Refresh Workflow](/screenshots/token_refresh.png)

**Description:**
A proactive maintenance workflow that ensures continuous connectivity with the Agorapulse API by managing OAuth2 Bearer tokens autonomously.

- **Operational Efficiency Logic:** Includes a custom JavaScript guard clause (`Check Business Hours`) that restricts execution to business hours (Mon-Fri, 09:00-18:00), reducing unnecessary API calls and server load by 70%.
- **Automated TTL Calculation:** Dynamically computes the token's 'Time-To-Live' and updates the PostgreSQL credentials vault (`Update DB Token`) before the current session expires.
- **Error Resilience:** Prevents the entire ETL pipeline from failing due to 401 Unauthorized errors by guaranteeing a fresh token is always available in the database.

### 2. Outlook Data Bridge (Human-in-the-Loop)

_(See `/1-get-team-input`)_
![Outlook Bridge Workflow](/screenshots/image.png)

**Description:**
A hybrid workflow that bridges the gap between manual reporting (Excel/CSV via Email) and the automated database ecosystem.

- **Automated Parsing:** Triggers on specific email subjects, extracts `.xlsx` attachments, and converts binary data to JSON.
- **Regex Normalization:** A robust JavaScript node (`Normalize IDs & Dates`) that extracts standardized IDs from diverse URL patterns (YouTube Shorts, Instagram Reels, TikTok VMs) to ensure database consistency.
- **Smart Deduplication:** Implements an **O(1) complexity lookup** using JavaScript `Sets` to compare incoming Excel rows against existing database records (`Filter Duplicates`), preventing duplicate entries more efficiently than standard SQL upserts.

### 3. Audience Metrics Ingestion (The Core Engine)

_(See `/2-get-audience_metrics`)_
![Core Engine Logic](/screenshots/image3.png)

**Description:**
The central pipeline responsible for fetching, normalizing, and storing granular engagement data (followers, impressions, reach) for all 23 connected accounts.

- **Smart Rate-Limiting:** Before execution, the system queries the `api_call_log` table to ensure the rolling 30-minute quota (500 calls) hasn't been breached. If the limit is near, the workflow halts to prevent API bans.
- **Rolling Window Logic:** A JavaScript node (`Calculate Date Range`) dynamically calculates the fetch period (Last 21 days from the previous Sunday) to ensure consistent weekly reporting windows.
- **Atomic Data Consistency:** Implements a "Delete-before-Write" strategy. It removes existing records for the target period (`Delete Old Data`) before inserting new data, guaranteeing **idempotency** (safely re-runnable without creating duplicates).
- **Batch Processing:** Uses `Loop Over Items` and `SplitInBatches` to process accounts sequentially, managing memory usage and API timeouts efficiently.

### 4. Hybrid Content Analytics (Social + SharePoint)

_(See `/3-get-content-metrics`)_

<div align="center">
  <img src="/screenshots/3_full_map.png" alt="Full Workflow Architecture" width="100%">
  <p><em>Figure A: Full Orchestration View</em></p>
</div>

#### Logic Detail (Zoom In):

The core differentiation logic handling multi-platform nuances:

<div align="center">
  <img src="/screenshots/3_logic_detail.png" alt="Logic Detail Switch Node" width="80%">
</div>

**Description:**
A specialized pipeline that fetches post-level performance data (Likes, Comments, Shares) and distributes it to both the SQL Data Warehouse and legacy SharePoint Excel reports.

- **Conditional Logic Routing:** Uses a `Switch` node (visible in zoom-in) to apply different extraction logic depending on the platform (e.g., separating Instagram "Stories" from "Feed Posts" via distinct API endpoints) and merging them back into a unified schema.
- **Hybrid Output Strategy:**
  - **SQL Stream:** Writes normalized data to PostgreSQL for Tableau/PowerBI dashboards.
  - **Legacy Stream:** Simultaneously appends processed rows to a corporate SharePoint Excel file (`Append Rows to Excel`) for teams that rely on spreadsheet reporting.
- **Advanced Data Cleaning:** Implements a two-step "Garbage Collection" mechanism in JavaScript (`Clean Empty Metrics`). It builds a Set of "valuable metrics" (non-zero) and filters out thousands of empty rows to keep the database lean.

### 5. Automated Data Mart Refresh

_(See `/4-refresh-materialized-views-postgreSQL`)_

**Description:**
The final step in the pipeline ensures that all BI dashboards (PowerBI/Tableau) serve fresh data at the start of the business week.

- **Scheduled Maintenance:** Triggers automatically every Monday at 03:40 AM (off-peak hours) to prevent database lock contention during working hours.
- **Batch Materialized View Refresh:** Executes a sequence of SQL `REFRESH MATERIALIZED VIEW` commands to pre-calculate complex aggregations (e.g., `auditoria_shorts_virales_21d`, `auditoria_viz_por_pieza_7d`). This moves the computational load away from the dashboard read-time, ensuring sub-second query performance for end-users.

---

## Privacy & Security Notice

**This is a showcase repository.**
To comply with corporate non-disclosure agreements (NDAs) and data privacy regulations:

1.  **Credentials Sanitized:** All API keys, OAuth tokens, and database passwords have been removed or replaced with placeholders (e.g., `SANITIZED_CREDENTIAL`).
2.  **Generic Data:** Screenshots and JSON files do not contain real proprietary metrics.
3.  **Logic Preservation:** The workflow structure, JavaScript transformation nodes, and SQL logic remain intact to demonstrate engineering capabilities.

---

## 🛠 Tech Stack

- **Orchestration:** n8n (Self-hosted on Docker)
- **Database:** PostgreSQL (with materialized views for reporting)
- **Scripting:** Node.js / JavaScript (Complex data transformations)
- **APIs Integrated:** Microsoft Graph, Meta Graph API, TikTok API, Agorapulse.
- **Tools:** FFmpeg (for video metadata extraction).
