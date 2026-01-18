# Enterprise Multi-Platform ETL Pipeline

![n8n](https://img.shields.io/badge/Orchestrator-n8n-FF6560?style=for-the-badge&logo=n8n&logoColor=white)
![Postgres](https://img.shields.io/badge/Database-PostgreSQL-336791?style=for-the-badge&logo=postgresql&logoColor=white)
![JavaScript](https://img.shields.io/badge/Scripting-JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![Docker](https://img.shields.io/badge/Deployment-Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

> **High-availability orchestration system managing data synchronization across 23 corporate social media accounts (TikTok, Meta, YouTube).**

## Project Overview

This repository documents the logic structure of a production-grade ETL (Extract, Transform, Load) pipeline designed to handle social metrics datasets without downtime.

The system serves as the integration layer between raw API data, manual Excel reporting, and a centralized Data Warehouse.

|       Challenges        |                             Engineering Solutions                              |
| :---------------------: | :----------------------------------------------------------------------------: |
|   Data fragmentation    |       Unified 23 accounts across 4 APIs into a single PostgreSQL Schema        |
|     API Instability     |          Implemented a self-healing OAuth2 rotation and retry Logic.           |
| Performance Bottlenecks | Offloaded complex aggregations to Materialized Views with automated refreshes. |
|     Data Integrity      |    Enforced Idempotency via "Delete-before-Write" and Optimized Filtering.     |

### Key Metrics

- **Scale:** Manages data for 23 distinct brand accounts.
- **Volume:** Processes daily engagement metrics via batched execution.
- **Reliability:** Implements automated token rotation and proactive rate-limiting logic.

---

## System Architecture & Orchestration

The following diagram illustrates the high-level infrastructure and the routing logic required to handle multiple data sources, platform quirks, and database upsert strategies.

![System Architecture Map](/screenshots/architecture.png)

---

## Workflow Modules

### 1. Self-Healing Authentication (Token Rotation)

_(See `/0-token-refresh`)_
![Token Refresh Workflow](/screenshots/0.png)

**Description:**
A proactive maintenance workflow that ensures continuous connectivity by managing OAuth2 Bearer tokens autonomously.

- **Operational Efficiency Logic:** Includes a custom JavaScript guard clause that restricts execution to business hours, reducing unnecessary API calls by 70%.
- **Predictive Refresh Logic:** Dynamically computes the token's 'Time-To-Live' and updates the PostgreSQL credentials vault before expiration.
- **Error Resilience:** Prevents pipeline downtime due to 401 Unauthorized errors by guaranteeing fresh credentials.

### 2. Outlook Data Bridge (Human-in-the-Loop)

_(See `/1-get-team-input`)_
![Outlook Bridge Workflow](/screenshots/1.png)

**Description:**
A hybrid workflow that transforms non-standardized human input (Excel/CSV) into production-ready data.

- **Pattern-based Data Sanitization:** Robust Regex Engine to extract standardized IDs from diverse URL patterns (Shorts, Reels, Stories).
- **Temporal Normalization:** Handles legacy system quirks by converting Excel serial dates (Epoch 1899) into ISO 8601 format.
- **Defensive Programming:** Strict guard clauses filter malformed data to protect the ingestion layer.

<details>
<summary><b>View JavaScript Implementation (Node.js)</b></summary>

```js
/**
 * Custom Transformation Logic for Data Normalization
 * Handles Regex pattern matching for Social Media URLs
 * and Excel serial date conversion.
 */

// Helper: Extract ID from heterogeneous URL patterns
function getNormalizedId(url) {
	if (!url || typeof url !== "string") return null;
	let match;

	// YouTube Patterns: watch, shorts, embed, youtu.be
	match = url.match(/(?:youtube\.com\/(?:watch\?v=|shorts\/|embed\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})/);
	if (match) return match[1];

	// Instagram Patterns: p, reel, stories
	match = url.match(/instagram\.com\/(?:p|reel|stories)\/(?:[a-zA-Z0-9._-]+\/)?([a-zA-Z0-9_-]+)/);
	if (match) return match[1];

	// TikTok Patterns: video or vm.tiktok.com
	match = url.match(/tiktok\.com\/.*\/video\/(\d+)|vm\.tiktok\.com\/([a-zA-Z0-9]+)/);
	if (match) return match[1] || match[2];

	// Facebook Patterns: reel, video, watch
	match = url.match(/(?:facebook\.com\/.*(?:videos|reel)\/|watch\/\?v=|fb\.watch\/)([a-zA-Z0-9_.-]+)/);
	if (match) return match[1];

	return null;
}

// Helper: Convert Excel Serial Date to ISO String
function excelDateToISO(serial) {
	const numSerial = parseFloat(serial);
	if (isNaN(numSerial) || numSerial < 1) return null;

	const excelEpoch = new Date("1899-12-30T00:00:00Z");
	const date = new Date(excelEpoch.getTime() + numSerial * 24 * 60 * 60 * 1000);

	return isNaN(date.getTime()) ? null : date.toISOString().slice(0, 10);
}

// Main Logic: Filter and Map
const allItems = $input.all();
const cleanItems = [];

for (const item of allItems) {
	const { ID, Fecha, Enlace, Cuenta, Célula, Tipo } = item.json;

	const convertedDate = excelDateToISO(Fecha);
	const normalizedId = getNormalizedId(Enlace);

	// Strict Data Validation
	if (ID && convertedDate && normalizedId) {
		cleanItems.push({
			json: {
				id_post: String(ID),
				cuenta: Cuenta,
				celula: Célula,
				enlace: Enlace,
				tipo: Tipo,
				fecha_publicacion: convertedDate,
				id_normalizado: normalizedId,
			},
		});
	}
}

return cleanItems;
```

</details>

### 3. Audience Metrics Ingestion (The Core Engine)

_(See `/2-get-audience_metrics`)_
![Core Engine Logic](/screenshots/2.png)

**Description:**
The central pipeline responsible for storing granular engagement data (followers, impressions, reach) for all 23 connected accounts.

- **Smart Rate-Limiting:** Queries api_call_log to ensure the rolling 30-minute quota hasn't been breached.
- **Atomic Data Consistency:** Implements a "Delete-before-Write" strategy, guaranteeing idempotency (safely re-runnable without duplicates).
- **Resource Management:** Uses n8n's batch-processing to manage memory usage and API timeouts efficiently.

### 4. Hybrid Content Analytics (Social + SharePoint)

_(See `/3-get-content-metrics`)_
![Hybrid Content Analytics](/screenshots/3.png)

**Description:**
Fetches post-level performance data and distributes it to both the SQL Data Warehouse and legacy SharePoint reports.

- **Conditional Logic Routing:** Separates platform-specific extraction logic (e.g., Instagram Stories vs. Feed Posts).

- **Advanced Data Cleaning:** Implements "Garbage Collection" logic in JS to filter out thousands of empty rows and keep the database lean.

### 5. Automated Data Mart Refresh

_(See `/4-refresh-materialized-views-postgreSQL`)_
![Automated Data Mart Refresh](/screenshots/4.png)

**Description:**
The final step in the pipeline ensures that all BI dashboards serve fresh data with sub-second performance.

- **Scheduled Maintenance:** Triggers automatically during off-peak hours to prevent database lock contention.
- **Batch Materialized View Refresh:** Executes SQL sequences to pre-calculate complex aggregations, moving computational load away from dashboard read-time.

---

## Key Engineering Patterns Applied

**Idempotency**: All workflows are designed to be safely re-runnable. The "Delete-before-Write" strategy ensures that partial failures don't result in corrupted datasets.

**Rate-Limit Awareness**: Monitoring of API quotas prevents 429 errors and service blacklisting.

**Optimized Filtering Logic**: Leveraging JavaScript Sets (where applicable) to ensure linear scalability as data volume increases.

**Separation of Concerns**: Distinct workflows for Authentication, Ingestion, and Optimization for easier maintenance and debugging.

## Privacy & Security Notice

**This is a showcase repository.**
To comply with corporate non-disclosure agreements (NDAs) and data privacy regulations:

1.  **Credentials Sanitized:** All API keys, OAuth tokens, and passwords have been replaced with placeholders.
2.  **Generic Data:** Screenshots and JSON files do not contain real proprietary corporate metrics.
3.  **Logic Preservation:** Workflow structures and custom transformation nodes remain intact for architectural showcase.

---

## Tech Stack

- **Orchestration**: n8n (Production-grade deployment via Docker & Docker Compose).
- **Persistence**: PostgreSQL (Relational Data Warehouse with optimized indexing).
- **Runtime**: Node.js (High-performance custom data transformation).
- **Infrastructure**: Self-hosted on a Linux VPS with automated backups.
