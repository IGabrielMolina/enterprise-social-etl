# Enterprise Multi-Platform ETL Pipeline (Social Data Engine)

![n8n](https://img.shields.io/badge/Orchestrator-n8n-FF6560?style=for-the-badge&logo=n8n&logoColor=white)
![Postgres](https://img.shields.io/badge/Database-PostgreSQL-336791?style=for-the-badge&logo=postgresql&logoColor=white)
![JavaScript](https://img.shields.io/badge/Scripting-JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![Docker](https://img.shields.io/badge/Deployment-Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

> **High-availability orchestration system managing data synchronization across 20+ corporate social media accounts (TikTok, Meta, YouTube).**

## Project Overview

This repository documents a production-grade ETL (Extract, Transform, Load) pipeline designed to process social metrics at scale without downtime. The system serves as the integration layer between raw API data and a centralized Data Warehouse, providing a unified source of truth for 20+ brand accounts.

| Challenges             | Engineering Solutions                                              |
| :--------------------- | :----------------------------------------------------------------- |
| **Data Fragmentation** | Unified 20+ accounts across 4 APIs into a single PostgreSQL Schema. |
| **API Quota Limits**   | Implemented high-performance Batching and O(1) Hash Mapping logic. |
| **Credential Decay**   | Developed a self-healing OAuth2 rotation and refresh logic.        |
| **Data Integrity**     | Enforced Idempotency via SQL Upserts and Composite Keys.           |

---

## System Architecture & Orchestration

The engine runs on a dedicated Linux VPS within **Docker** containers. It leverages **Custom Node.js Logic** to handle complex transformations that standard orchestrator nodes cannot manage efficiently, ensuring high throughput and low latency.

![System Architecture Map](/screenshots/architecture.png)

---

## Workflow Modules

### 0. Identity & Access Management (Token Refresh)

[See Token Refresh Logic](./0-%20token-refresh)

The system's "security heartbeat." It maintains continuous connectivity by autonomously managing the OAuth2 lifecycle for all platform APIs.

- **Predictive Refresh Logic:** Dynamically computes credential _Time-To-Live_ (TTL) and updates the PostgreSQL vault before expiration.
- **Zero-Downtime Reliability:** Eliminates 401 Unauthorized errors by guaranteeing fresh Bearer tokens for every ingestion cycle.

### 1. TikTok Ingestion (Granular Content Metrics)

[See TikTok Workflows](./1-%20TikTok)
![TikTok Post Metrics](/screenshots/Tiktok-1.png)
![TikTok Account Metrics](/screenshots/Tiktok-2.png)

Responsible for fetching performance data from the TikTok Marketing API.

- **Hierarchical JSON Flattening:** Custom logic to transform deep nested engagement arrays into relational rows.
- **ID Normalization:** Standardizes video identifiers to ensure consistent historical tracking across the data series.

### 2. Meta Logic (Facebook & Instagram)

[See Meta Workflows](./2-%20Meta)
![Meta Post Metrics](/screenshots/meta-1.png)
![Meta Account Metrics](/screenshots/meta-2.png)

Massive management of 23 profiles with dynamic brand segmentation.

- **Temporal Precision (Luxon):** Forces all data processing into the `America/Argentina/Buenos_Aires` timezone. This ensures daily snapshots represent an exact 24-hour window regardless of server location.
- **Dynamic Metadata Injection:** Enriches raw streams with account names and platform identifiers to support efficient database partitioning.

### 3. YouTube Analytics (High-Performance Core)

[See YouTube Workflows](./3-%20Youtube)
![YouTube Update IDs](/screenshots/youtube-1.png)
![YouTube Post Metrics](/screenshots/youtube-2.png)
![YouTube Account Metrics](/screenshots/youtube-3.png)

This is the most advanced module, engineered to bypass Google API bottlenecks and maximize ingestion speed.

- **Batch Processing Engine:** Instead of iterating per item, the system aggregates IDs into **500-unit batches**, drastically reducing round-trips and API credit consumption.
- **O(1) Hash Mapping:** Implements in-memory object maps to cross-reference publish dates and metrics in constant time. This prevents nested-loop performance degradation, keeping execution time flat as volume grows.
- **Dynamic Time-Windowing:** Uses advanced date logic with a 5-day lag to capture consolidated
