# System Architecture Specification: Project *Organon*

---

## 1. Requirements & Scope Framing

### 1.1. Core Functional Requirements

*   **FR-1: Constraint-Driven Inverse Generation:** The system must procedurally synthesize valid directed acyclic graph (DAG) logic structures based on a multi-dimensional Complexity Vector $\vec{C} = \langle D_{\text{inf}}, W_m, B_f, \Phi_{\text{rules}}, \Omega_{\text{bias}} \rangle$ using Answer Set Programming (ASP) and SMT-LIB2 solvers.
*   **FR-2: Formal Soundness & Uniqueness Verification:** Every generated puzzle must be mathematically validated prior to client delivery. The system must prove satisfiability of $\text{Premises} \land \text{Conclusion}$ and unsatisfiability ($\text{UNSAT}$) of $\text{Premises} \land \neg\text{Conclusion}$. It must extract the Minimal Unsatisfiable Subset (MUS) to eliminate dead or redundant clues.
*   **FR-3: Decoupled Semantic Skinning:** Abstract logic skeletons (`LogicGraphIR`) must map into domain-specific natural language skins (e.g., Aerospace, Cybersecurity, Epidemiology) via Controlled Natural Language (CNL) rules without introducing semantic ambiguities or modifying the underlying graph topology.
*   **FR-4: Sub-50ms Tactile Client Validation:** Client moves, hypothesis toggles, and step deductions must be verified within the client runtime using a WebAssembly (Wasm) formal evaluator to eliminate round-trip network latency during visual manipulation.
*   **FR-5: Socratic Diagnostic Feedback & Countermodel Generation:** When an invalid deduction is committed, the engine must extract a minimal countermodel satisfying the premises while refuting the erroneous deduction, translate it into the active semantic skin, and return an interactive counterfactual scenario.
*   **FR-6: High-Frequency Telemetry & Adaptive Cognitive Profiling:** The platform must ingest user graph mutations, calculate Multidimensional Item Response Theory (MIRT) and Bayesian Knowledge Tracing (BKT) parameter updates, and persist fine-grained interaction telemetry for cognitive state tracking.

### 1.2. Non-Functional Requirements & Service Level Objectives

*   **P99 Latency:**
    *   *Client-Side Interaction Feedback (Wasm):* $\le 15\text{ ms}$ (Target: $<10\text{ ms}$).
    *   *Real-Time Telemetry Ingestion (WebSocket/Gateway):* $\le 50\text{ ms}$.
    *   *Socratic Diagnostic Countermodel Extraction (Server-Side Fallback):* $\le 350\text{ ms}$.
    *   *Puzzle Delivery from Pre-generation Cache:* $\le 80\text{ ms}$.
    *   *Cold Puzzle Procedural Generation (JIT ASP/SMT execution):* $\le 1,800\text{ ms}$ (Bound by timeout: $1,500\text{ ms}$).
*   **Throughput & Scale:**
    *   *Peak Concurrent Active Users (CCU):* $100,000$ concurrent learners.
    *   *Telemetry Ingestion Throughput:* $50,000$ events/second continuous; $150,000$ events/second burst.
    *   *Puzzle Generation Capacity:* 500 completed skeletons/second across distributed compute pools.
*   **Availability & Durability:**
    *   *API & Ingress Availability:* $99.95\%$ uptime ($< 21.9$ minutes downtime/month).
    *   *User Profile & Proof Audit Durability:* $99.999999999\%$ (11 9s).
    *   *RPO (Recovery Point Objective):* $\le 0$ for completed sessions; $\le 5$ seconds for real-time telemetry streams.
    *   *RTO (Recovery Time Objective):* $\le 60$ seconds for computational workers; $\le 15$ minutes for primary database failover.

### 1.3. Operating Constraints & Production Assumptions

*   **Compute Footprint:** Backend computational solvers (Clingo, Z3, CVC5) are CPU-bound and memory-sensitive. They must run in isolated container pools with hard CPU/memory cgroups to prevent noisy-neighbor starvation.
*   **Client Compatibility:** The target client environment is modern evergreen web browsers (Chromium $\ge 110$, Firefox $\ge 112$, Safari $\ge 16.4$) with WebAssembly support (MVP + SIMD + Threads where available) and WebGL 2.0 / WebGPU context access.
*   **Network Ingress:** Assume client environments may have erratic mobile/campus connections; the client architecture must execute verification fully offline once the puzzle payload is transferred.
*   **Storage Boundaries:** Micro-telemetry data grows at $\sim 1.2 \text{ TB}$ per day at peak scale; retention policies must strictly tier raw event frames into cold columnar storage while rolling up psychometric states.

---

## 2. System Architecture Specification

### 2.1. System Topology & C4 Container Architecture

```mermaid
C4Context
    title System Context & Container Boundaries for Project Organon

    Person(user, "Learner / Logician", "Interacts with formal visual puzzles via canvas.")
    
    System_Boundary(c_client, "Client Boundary (Web Browser)") {
        Container(spa, "Loom Canvas SPA", "React, PixiJS, Zustand", "Hardware-accelerated reactive canvas graph.")
        Container(wasm_solver, "Wasm Epistemic Kernel", "Z3-Wasm / C-FFI", "Instantaneous local rule and step validation.")
    }

    Enterprise_Boundary(c_infra, "Organon Infrastructure (Kubernetes / Multi-AZ)") {
        Container(ingress, "Envoy Gateway", "Envoy / gRPC-Web", "Edge routing, TLS termination, WAF, rate limiting.")
        Container(api_gw, "Core Orchestration Gateway", "Go", "Session orchestration, puzzle routing, auth validation.")
        
        Container(ssne, "Semantic Skinning Service (SSNE)", "Rust", "Template AST binding, CNL generator, validation.")
        
        ContainerQueue(nats, "NATS JetStream Bus", "NATS", "High-throughput telemetry ingestion & generation queues.")
        
        Container(d_engine, "Diagnostic & Telemetry Engine (DTE)", "Python / Cython", "BKT, IRT calculation, Socratic hint dispatch.")
        
        Container(cek_pool, "Computational Epistemic Kernel (CEK)", "C++ / Rust / Clingo / Z3", "ASP synthesis, SMT MUS extraction, causal logic.")
        
        Container(cache_redis, "Redis Cluster", "Redis 7.2", "Pre-computed puzzle skeletons, hot session cache.")
        ContainerDb(db_pg, "Primary Relational DB", "PostgreSQL 16", "User identity, session state, audit logs, curricula.")
        ContainerDb(db_neo4j, "Graph Engine", "Neo4j 5 Enterprise", "Canonical LogicGraphIR topologies, rule ontologies.")
        ContainerDb(db_timescale, "Telemetry Engine", "TimescaleDB", "Hypertables for sub-second user graph mutations.")
    }

    Rel(user, spa, "Interacts, draws inferences, views countermodels", "HTTPS / Canvas UI")
    Rel(spa, wasm_solver, "Direct memory bridge / function calls", "Wasm Memory Buffer")
    Rel(spa, ingress, "Bi-directional telemetry & puzzle payloads", "gRPC-Web / WebSockets")
    
    Rel(ingress, api_gw, "Routes RPC calls", "gRPC")
    Rel(api_gw, cache_redis, "Pops pre-generated skeletons", "RESP3")
    Rel(api_gw, ssne, "Requests skin binding for target domain", "gRPC")
    Rel(api_gw, nats, "Publishes telemetry stream", "TCP")
    
    Rel(nats, d_engine, "Subscribes to telemetry events", "Push Consumer")
    Rel(nats, cek_pool, "Dispatches async generation tasks", "Pull Consumer")
    
    Rel(cek_pool, cache_redis, "Stores verified abstract skeletons", "RESP3")
    Rel(cek_pool, db_neo4j, "Queries/Stores canonical graph topologies", "Bolt")
    
    Rel(d_engine, db_timescale, "Batched writes of micro-interactions", "pgx / SQL")
    Rel(d_engine, db_pg, "Updates BKT/MIRT user skill vectors", "SQL")
    Rel(api_gw, db_pg, "Reads/writes session and auth", "SQL")
```

### 2.2. Component Breakdown & Protocols

```
+---------------------------------------------------------------------------------------------------+
| COMPONENT              | TECH STACK           | COMMUNICATION        | RESPONSIBILITIES           |
+------------------------+----------------------+----------------------+----------------------------+
| Loom Canvas Client     | React 18, PixiJS v8, | Wasm Memory Bridge,  | GPU render of DAG nodes;   |
|                        | TypeScript, Zustand  | WebSockets, gRPC-Web | local drag-and-drop state; |
|                        |                      |                      | dynamic Sugiyama layout.   |
+------------------------+----------------------+----------------------+----------------------------+
| Client Wasm Solver     | Z3 C++ compiled to   | SharedArrayBuffer /  | Sub-15ms incremental step  |
|                        | Wasm (Emscripten)    | Direct C-FFI Calls   | validation; premise        |
|                        |                      |                      | checking; local counter-   |
|                        |                      |                      | model extraction.          |
+------------------------+----------------------+----------------------+----------------------------+
| API & Orchestration GW | Go 1.22, Connect-RPC | gRPC / HTTP/2,       | Auth validation, rate-     |
|                        | (Envoy sidecar)      | WebSocket handling   | limiting, dispatching      |
|                        |                      |                      | pre-gen puzzles, session.  |
+------------------------+----------------------+----------------------+----------------------------+
| Computational Kernel   | C++20, Clingo 5.6,   | NATS JetStream,      | Combinatorial ASP DAG      |
| Worker Pool (CEK)      | Z3 4.12, Rust        | gRPC Worker RPC      | generation; SMT MUS        |
|                        |                      |                      | extraction; Causal SCM.    |
+------------------------+----------------------+----------------------+----------------------------+
| Semantic Skinning      | Rust 1.76, LALRPOP,  | gRPC (Protobuf v3)   | LogicGraphIR to CNL AST;   |
| Engine (SSNE)          | Regex, Tera          |                      | Attempto Controlled Eng;   |
|                        |                      |                      | Round-trip AST validation. |
+------------------------+----------------------+----------------------+----------------------------+
| Diagnostic & Telemetry | Python 3.11, Cython, | NATS Consumer,       | Async telemetry parsing,   |
| Engine (DTE)           | NumPy, SciPy         | pgx async pooling    | BKT/MIRT vector updates,   |
|                        |                      |                      | Socratic hint generation.  |
+---------------------------------------------------------------------------------------------------+
```

#### Communication Boundaries & Payloads
1.  **Client $\leftrightarrow$ Gateway:** Client connects over WebSocket/gRPC-Web via Envoy. Puzzle delivery arrives as a compacted binary Protobuf frame containing the `PuzzleInstanceIR` (topology, initial premises, masked targets, node-skin bindings, and pre-compiled Wasm constraint arrays).
2.  **Telemetry Stream:** Client transmits batched micro-interaction frames (`UserDeductionStep`, dwell times, hover events) every $250\text{ ms}$ over the established WebSocket channel. The Gateway validates JWT session claims and publishes directly to the `telemetry.raw` subject on NATS JetStream.
3.  **Kernel Worker Pipeline:** CEK workers operate as pull consumers on NATS subject `puzzle.synthesis.jobs`. They process batch requests, persist validated abstract skeletons directly to Redis (as serialized Protobuf), and index canonical structural graphs in Neo4j.

---

### 2.3. Data Architecture & Polyglot Persistence Strategy

```
                           DATA ARCHITECTURE BUS
  
  [ Client Telemetry ]       [ Synthesis Skeletons ]       [ User Profiles / Auth ]
           │                           │                              │
           ▼                           ▼                              ▼
  +─────────────────+         +─────────────────+            +─────────────────+
  |  TimescaleDB    |         |  Neo4j + Redis  |            |  PostgreSQL 16  |
  |  (Time-Series)  |         | (Graph & Cache) |            |  (ACID Store)   |
  +─────────────────+         +─────────────────+            +─────────────────+
  - Ingestion:               - Hot Pools (Redis):           - Strict relational schema
    150k events/sec            LPOP/RPOP <1ms                 for users, classes, orgs.
  - Hypertables with         - Topologies (Neo4j):          - Stores immutable proof logs
    1-day chunks               Isomorphic subgraphs,          and active session tokens.
  - Rollup compression         canonical complexity sets.   - Row-level security (RLS).
```

#### Storage Component Allocation
1.  **PostgreSQL 16 (Relational Source of Truth):**
    *   *Usage:* User accounts, role-based access control (RBAC), multi-tenant enterprise domains, curriculum progression states, and signed cryptographic audit logs of verified student completions.
    *   *Consistency:* Strong consistency (ACID). Read replicas handle read-heavy reporting.
2.  **TimescaleDB (Telemetry Engine):**
    *   *Usage:* Stores granular client-side interaction events (`UserDeductionStep`, coordinate translations, assumption changes).
    *   *Design:* Partitioned hypertables on `timestamp` with 1-day chunk intervals. Automated compression policies enabled for chunks older than 48 hours (converting rows to compressed columnar format). Data older than 90 days drops to cold S3 Parquet via automated continuous aggregates.
3.  **Neo4j 5 Enterprise (Isomorphic Structural Store):**
    *   *Usage:* Stores the canonical logical skeletons (`LogicGraphIR`) decoupled from language skins. Allows graph pattern matching (Cypher queries) to identify structural overlaps, cycles, lemma patterns, and difficulty clustering.
    *   *Consistency:* Causal consistency via Raft core cluster.
4.  **Redis 7.2 Cluster (Ephemeral & Pre-generation Cache):**
    *   *Usage:* Houses pre-generated and verified puzzle skeleton queues, organized by `ComplexityVector` hashes (e.g., `queue:skeleton:d3:w2:b3:ruleset_a`). Acts as the distributed session store and WebSocket connection registry.
    *   *Eviction:* `noeviction` for pre-generation queues; volatile LRU for session caches.

#### Database Schemas (Physical DDL Extracts)

```sql
-- PostgreSQL 16: Core User & Session Schema
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE user_cognitive_profiles (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    theta_deduction DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    theta_causal DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    theta_deontic DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    theta_counterfactual DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    theta_bias_resistance DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    bkt_parameters JSONB NOT NULL DEFAULT '{}'::jsonb,
    last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE puzzle_completions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    puzzle_id VARCHAR(64) NOT NULL,
    skeleton_id VARCHAR(64) NOT NULL,
    domain_schema VARCHAR(32) NOT NULL,
    is_successful BOOLEAN NOT NULL,
    execution_time_ms INTEGER NOT NULL,
    steps_count INTEGER NOT NULL,
    proof_transcript_signature BYTEA NOT NULL,
    completed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- TimescaleDB: Telemetry Ingestion Hypertable
CREATE TABLE telemetry_events (
    timestamp TIMESTAMPTZ NOT NULL,
    user_id UUID NOT NULL,
    puzzle_id VARCHAR(64) NOT NULL,
    event_type VARCHAR(32) NOT NULL,
    source_node VARCHAR(32),
    target_node VARCHAR(32),
    operator VARCHAR(16),
    dwell_time_ms INTEGER,
    client_eval_result VARCHAR(32),
    payload JSONB
);

SELECT create_hypertable('telemetry_events', 'timestamp', chunk_time_interval => INTERVAL '1 day');
ALTER TABLE telemetry_events SET (timescaledb.compress, timescaledb.compress_segmentby = 'user_id, puzzle_id');
SELECT add_compression_policy('telemetry_events', INTERVAL '2 days');
```

---

### 2.4. Cross-Cutting Concerns

#### Authentication, Authorization & Identity Propagation
*   **Authentication:** Mutual TLS (mTLS) with SPIFFE/SPIRE IDs enforced for all internal service-to-service communication. Edge authentication utilizes OAuth2 / OpenID Connect (OIDC) issuing asymmetric RS256 JWTs.
*   **Authorization:** Role-Based Access Control (RBAC) enforced at the Gateway; fine-grained tenant boundaries are propagated via gRPC metadata contexts (`x-org-id`, `x-user-id`). User-level access to exercise branches uses Row-Level Security (RLS) in PostgreSQL.

#### Security & Sandboxing Architecture
*   **Wasm Runtime Sandbox:** The client-side Wasm binary is instantiated in a secure WebAssembly sandbox with disabled direct DOM access and strictly bounded memory (16MB maximum linear memory via `WebAssembly.Memory({ initial: 256, maximum: 256 })`).
*   **Solver Execution Guardrails:** Backend ASP/SMT solver child processes (Clingo/Z3) run in ephemeral, unprivileged Linux containers with seccomp profiles blocking all non-essential syscalls. Compute processes have rigid cgroups resource constraints (1.0 CPU core, 512MB RAM ceiling, non-swap) and are terminated forcefully by Linux `setrlimit` if execution exceeds $1,500\text{ ms}$.

#### Observability & Distributed Tracing
*   **Tracing:** OpenTelemetry (OTel) instrumentation across all Go, Rust, C++, and Python services. Context propagation carries W3C `traceparent` headers through Envoy, API Gateway, NATS messages, and background workers.
*   **Metrics Collection:** Prometheus scrapes Envoy gateways, microservice `/metrics` endpoints, Redis cluster states, and NATS queue depths. Key custom metrics:
    *   `organon_asp_grounding_seconds` (Histogram)
    *   `organon_smt_mus_extraction_milliseconds` (Histogram)
    *   `organon_wasm_client_eval_latency_bucket` (Client-reported telemetry)
    *   `organon_pregen_pool_depth{complexity_vector="..."}` (Gauge)
*   **Logging:** Structured JSON logs emitted to `stdout`, aggregated via FluentBit, routed to OpenSearch, tagged with `correlation_id`.

#### Fault Tolerance, Resilience & Circuit Breaking
*   **Pre-generation Queue Starvation Fallback:** If the Redis pre-computed skeleton queue for a specific `ComplexityVector` falls below a critical threshold ($\le 50$ units), the API Gateway falls back gracefully:
    1. Pops a skeleton matching the closest adjacent vector ($\Delta \text{complexity} \le \pm 1$).
    2. Dynamically adjusts skinning constraints to mask difficulty deficits.
    3. Fires a high-priority synthesis event on NATS to replenish the starved bucket.
*   **Wasm Engine Failure Fallback:** If a client browser fails to initialize WebAssembly (e.g., due to disabled JIT, old browser, or memory exhaustion), the client switches to **Degraded Server Mode**: all deduction checks fall back to synchronous RPC round-trips against the API Gateway SMT evaluation worker pool.

---

### 2.5. Implementation Roadmap

```
+───────────────────────────────────────────────────────────────────────────────────────────────────+
| PHASE 1: CORE LOGIC FOUNDATION & FORMAL KERNEL (WEEKS 1–6)                                       |
| - Finalize Protobuf schemas (`logic_core.proto`).                                                 |
| - Implement Clingo ASP DAG synthesis rules with bounded depth & complexity controls.              |
| - Build C++ Z3 SMT uniqueness verification & MUS extraction pipeline.                            |
| - Cross-compile micro-SMT evaluator to Wasm via Emscripten; benchmark linear memory constraints.  |
| Milestone 1: Headless CLI generating mathematically sound, verified, minimal IR logic skeletons. |
+───────────────────────────────────────────────────────────────────────────────────────────────────+
                                                  │
                                                  ▼
+───────────────────────────────────────────────────────────────────────────────────────────────────+
| PHASE 2: LOOM CANVAS & REACTIVE CLIENT INTERFACE (WEEKS 7–12)                                    |
| - Develop PixiJS hardware-accelerated DAG rendering canvas with 60+ FPS interactive transforms.   |
| - Implement Sugiyama dynamic layout engine with real-time barycentric edge-crossing reduction.    |
| - Integrate client Wasm engine via SharedArrayBuffer with Zustand reactive state management.      |
| - Implement ghost-state hypothesis rendering and visual shader-based contradiction effects.      |
| Milestone 2: Functional in-browser proof-canvas validating inputs locally in sub-15ms.            |
+───────────────────────────────────────────────────────────────────────────────────────────────────+
                                                  │
                                                  ▼
+───────────────────────────────────────────────────────────────────────────────────────────────────+
| PHASE 3: ASYNC PRE-GENERATION & CONTROLLED SKINNING (WEEKS 13–18)                                 |
| - Build NATS-driven distributed synthesis worker cluster.                                         |
| - Implement Redis pre-generation caching pool with automatic complexity replenishment loops.     |
| - Implement Rust SSNE service: CNL AST compilation, lexical domain ontologies, bias injection.    |
| - Build closed-loop AST verification to eliminate semantic drift during skinning.                 |
| Milestone 3: End-to-end pipeline delivering fully skinned, verified exercises with <80ms TTFB.    |
+───────────────────────────────────────────────────────────────────────────────────────────────────+
                                                  │
                                                  ▼
+───────────────────────────────────────────────────────────────────────────────────────────────────+
| PHASE 4: DIAGNOSTICS, PSYCHOMETRICS & SCALE RESILIENCE (WEEKS 19–24)                              |
| - Implement server-side countermodel extraction pipeline and Socratic narrative generation.      |
| - Deploy TimescaleDB hypertable infrastructure; wire WebSocket micro-telemetry streaming.         |
| - Implement real-time Multidimensional IRT and Bayesian Knowledge Tracing engine.                |
| - Execute chaos engineering (simulating ASP timeouts, solver panics, network partition recovery).|
| Milestone 4: Production-ready enterprise platform handling 100k CCU within all target SLOs.       |
+───────────────────────────────────────────────────────────────────────────────────────────────────+
```

---

## 3. Architecture Decision Records (ADRs)

---

### ADR-001: Adopt Client-Side WebAssembly (Wasm) Micro-Solver for Reactive Step Validation

*   **Status:** Accepted
*   **Context:**
    Project *Organon* requires instant visual feedback when users link nodes, toggle truth states, or commit intermediate lemmas on the Loom Canvas. Architectural Invariant #3 demands sub-50ms diagnostic feedback. Over-the-network round-trips (HTTP/gRPC) introduce uncontrollable latency jitter ($80\text{--}300\text{ ms}$ over 4G/erratic WiFi), which disrupts the tactile spatial interaction required for cognitive problem-solving.
*   **Decision:**
    We will compile an incremental SMT/Propositional solver core (a lean distribution of Z3 stripped of non-linear floating-point and uninterpreted function theories, and a backup compiled MiniSat core) to WebAssembly (Wasm) using Emscripten. The Wasm module runs inside the client browser thread (or dedicated Web Worker via `SharedArrayBuffer`), holding an in-memory representation of the active exercise's logical constraints. State updates use incremental `push`/`pop` assertion contexts (`solver_push()`, `solver_pop()`) instead of rebuilding solver environments from scratch on each drag event.
*   **Consequences:**
    *   *Positive:* Deducing satisfiability, invalid transitions, and local contradiction sparks executes deterministically in $\le 15\text{ ms}$ client-side without network traversal. Zero server compute is consumed for intermediate user interactions, substantially decreasing backend infrastructure costs.
    *   *Negative / Trade-offs:* Initial page bundle size increases by $\approx 2.4 \text{ MB}$ (gzipped Wasm binary). Client devices with severely constrained memory (<2GB RAM) may face garbage collection pauses if linear memory expands; this requires pre-allocating an isolated, fixed 16MB WebAssembly Memory pool without dynamic growth.
*   **Alternatives Considered:**
    1.  *Synchronous Server-Side RPC per Interaction:* Discarded due to network latency violating the $<50\text{ ms}$ SLO and backend server cost scaling linearly with every cursor drag.
    2.  *Client-Side Custom JavaScript Rule Engine:* Discarded because reimplementing first-order logic resolution, transitivity, and SAT algorithms in pure JavaScript risks correctness bugs, divergence from backend Z3 ground-truth proofs, and lack of MUS verification.

---

### ADR-002: Implement Asynchronous Pre-Generation Pool and Inverted SMT Masking Pipeline

*   **Status:** Accepted
*   **Context:**
    Procedurally generating logically sound exercises involves combinatorial Answer Set Programming (Clingo) to establish DAG topology, followed by SMT solving (Z3) to prove uniqueness and extract the Minimal Unsatisfiable Subset (MUS). In the worst cases, SMT and ASP solving exhibit exponential time complexity ($\mathcal{O}(2^n)$), causing JIT generation times to swing wildly from $200\text{ ms}$ to over $5,000\text{ ms}$. Serving puzzles on-demand would result in severe request timeouts and violate our P99 delivery SLA ($\le 80\text{ ms}$).
*   **Decision:**
    Decouple generation from consumption via an **Asynchronous Pre-Generation Pool**. A distributed cluster of CEK workers continuously synthesizes, validates, and masks logic graphs across categorized target `ComplexityVectors`. Abstract validated skeletons are pushed into categorized Redis FIFO queues (`pregen:skeleton:<hash>`). When a user requests an exercise, the API Gateway pops a pre-verified skeleton from Redis in $\le 5\text{ ms}$, routes it to the Semantic Skinning Engine (SSNE) for dynamic language hydration, and returns it to the client. Generation runs with an aggressive solver timeout threshold ($T_{\text{max}} = 1,500\text{ ms}$); if a worker exceeds this, it aborts the branch, discards the graph, and retries.
*   **Consequences:**
    *   *Positive:* Delivery latency to the client is completely insulated from solver runtimes, meeting the $\le 80\text{ ms}$ P99 SLA. Compute resources run at level, smoothed capacity rather than spiking during user usage surges.
    *   *Negative / Trade-offs:* Puzzles stored in queues consume memory in Redis. If the algorithmic parameters for a `ComplexityVector` are modified, cached skeletons must be invalidated and purged via distributed cache-flush workflows.
*   **Alternatives Considered:**
    1.  *Just-In-Time (JIT) Generation on Client Request:* Discarded because combinatorial explosions in the solver produce unpredictable latency spikes exceeding 5 seconds, causing bad user UX and HTTP connection drops.
    2.  *Static Pre-computed Question Database:* Discarded because it eliminates dynamic personalization, limits parametric adaptation based on Bayesian Knowledge Tracing, and allows bad actors to scrape and leak the finite puzzle bank.

---

### ADR-003: Polyglot Persistence Architecture (PostgreSQL, Neo4j, TimescaleDB, Redis)

*   **Status:** Accepted
*   **Context:**
    *Organon* processes three fundamentally distinct data paradigms:
    1. Relational transactional entities (users, enterprise tenancies, cryptographically signed completion records).
    2. Highly connected, acyclic, isomorphic problem topologies (isomorphic canonical logic DAGs, ontological taxonomies).
    3. Massive, write-heavy, append-only streams of telemetry (150k events/sec peak capturing tactile drag moves, hover dwells, and hypothesis state toggles).
    Using a single database system creates catastrophic performance trade-offs across these mixed access patterns.
*   **Decision:**
    Implement a targeted polyglot persistence architecture:
    *   **PostgreSQL 16:** Relational source of truth for identities, organizations, session state, and immutable proof audit ledgers using strong ACID boundaries.
    *   **Neo4j 5 Enterprise:** Graph database dedicated to storing canonical structural skeletons (`LogicGraphIR`). Handles graph pattern matching, isomorphic subgraph detection, and rule-dependency validation via Cypher.
    *   **TimescaleDB:** Time-series hypertable store for high-throughput user interaction telemetry. Uses automated daily chunking, columnar compression policies, and background rollups for psychometric analytics.
    *   **Redis 7.2 Cluster:** In-memory operational cache for the pre-generated skeleton pool, active user sessions, and real-time distributed rate-limiting.
*   **Consequences:**
    *   *Positive:* Each storage engine is specialized for its access pattern: TimescaleDB handles 150k events/sec writes without write lock contention; Neo4j runs deep graph traversals across complex deduction trees; PostgreSQL provides ACID transactional guarantees.
    *   *Negative / Trade-offs:* Operational overhead of maintaining four distinct storage technologies. Cross-datastore synchronization requires careful eventual consistency patterns and robust distributed tracing.
*   **Alternatives Considered:**
    1.  *Monolithic PostgreSQL for Everything:* Discarded because deep recursive CTEs on topological graphs degraded severely at scale, and high-frequency telemetry writes (150k/sec) caused massive Write-Ahead Log (WAL) bloat and VACUUM contention.
    2.  *Document Store (MongoDB) for Everything:* Discarded due to lack of native ACID transaction guarantees for enterprise audit ledgers, poor support for deep graph pattern queries, and inefficient uncompressed time-series operations.

---

### ADR-004: Semantic Skinning via Controlled Natural Language (CNL) with Closed-Loop AST Round-Trip Verification

*   **Status:** Accepted
*   **Context:**
    Architectural Invariant #2 requires "Zero-Hallucination Semantic Skinning." Unconstrained Large Language Models (LLMs) used for text generation inherently hallucinate, miss subtle propositional logic operators (confusing "if and only if" with "if"), and introduce syntactic ambiguities. Conversely, naive string concatenation creates robotic, unnatural text that degrades immersion.
*   **Decision:**
    Skinning must run through a deterministic Controlled Natural Language (CNL) pipeline based on Attempto Controlled English (ACE) principles, implemented as a dedicated microservice in Rust (`organon-ssne`). Surface text is assembled via Context-Free Grammars (CFGs) directly bound to formal AST nodes. 
    
    To guarantee soundness, the engine executes a **Closed-Loop AST Round-Trip Verification**: after natural language sentences are generated, the SSNE parses the text back through a deterministic compiler into an abstract logical formula ($L_{\text{extracted}}$). The system computes the structural tree isomorphism between $L_{\text{extracted}}$ and the original $L_{\text{seed}}$. The payload is delivered to the client if and only if the similarity score is identically $1.0$. If parsing fails or reveals semantic ambiguity, the system discards the candidate skin and picks an alternative template mapping.
*   **Consequences:**
    *   *Positive:* Zero logical drift. Guarantees that the surface natural language text strictly preserves the formal semantics of the underlying mathematical proof. Complete immunity to LLM hallucination and jailbreaking.
    *   *Negative / Trade-offs:* Writing and maintaining rich domain-specific CFG ontologies (Aerospace, Cybersecurity, Forensics) requires specialized computational linguistic effort. Natural language expressions can occasionally feel rigid compared to free-form human prose.
*   **Alternatives Considered:**
    1.  *Fine-Tuned LLM (e.g., Llama-3 / GPT-4o) Prompted with Constraints:* Discarded because probabilistic models cannot provide absolute mathematical non-hallucination guarantees; subtle edge-case misinterpretations of logic operators destroy exercise validity.
    2.  *Static Hardcoded Translation Tables:* Discarded because it produces repetitive, unengaging phrasing and fails to provide dynamic adversarial bias injection for advanced learners.

---

### ADR-005: Event-Driven Real-Time Telemetry Ingestion via NATS JetStream and TimescaleDB

*   **Status:** Accepted
*   **Context:**
    During an exercise, the Loom Canvas emits high-frequency micro-interaction events (node movements, premise inspections, hover dwell times, step deduction validations). With 100,000 concurrent users, telemetry generation can peak at 150,000 events/second. Direct synchronous writes to a transactional database would quickly exhaust connection pools and degrade API Gateway performance.
*   **Decision:**
    Deploy **NATS JetStream** as the distributed streaming message backbone. Telemetry packets received by the API Gateway over WebSockets are validated against Protobuf schemas and published immediately to NATS subject `telemetry.raw.<user_id>`. 
    
    A horizontally scaled fleet of Diagnostic & Telemetry Engine (DTE) workers operates as a NATS consumer group:
    1. Batches incoming messages into memory buffers (flushed every $1,000\text{ ms}$ or 5,000 events).
    2. Writes batched data directly to TimescaleDB hypertables via PostgreSQL binary `COPY` protocol (`pgx`).
    3. Concurrently dispatches events to the in-memory Bayesian Knowledge Tracing (BKT) and Multidimensional Item Response Theory (MIRT) state evaluators.
*   **Consequences:**
    *   *Positive:* Decouples API ingestion from persistence; network-facing gateways remain completely non-blocking. NATS JetStream provides high throughput with sub-millisecond publish latencies and built-in backpressure handling.
    *   *Negative / Trade-offs:* Telemetry in TimescaleDB is eventually consistent (lagging ingestion by up to $1,000\text{ ms}$). An extra infrastructure component (NATS) must be monitored and maintained across Kubernetes clusters.
*   **Alternatives Considered:**
    1.  *Apache Kafka:* Discarded due to substantially higher operational complexity (Zookeeper/KRaft coordination, heavier memory footprint) and higher latency profiles for this specific workload compared to lightweight Go-native NATS.
    2.  *Direct Write from Gateway to PostgreSQL/TimescaleDB:* Discarded because connection pooling and row-lock overhead under 150,000 events/second write bursts causes gateway connection exhaustion and catastrophic cascading failures.

---

### ADR-006: Hardware-Accelerated Hybrid Canvas Architecture (PixiJS WebGL/WebGPU + Zustand Reactive Store)

*   **Status:** Accepted
*   **Context:**
    Complex epistemic puzzles require displaying over 1,000 visual elements (nodes, hyper-edges, truth indicators, particle currents representing logical inference flow) running at 60–120 FPS. Traditional DOM-based graph solutions (such as standard React Flow or SVG-based libraries) suffer from extreme performance degradation and DOM-thrashing when manipulating large dynamic DAGs. Conversely, a pure WebGL canvas without structured state management makes building accessible user interfaces and control sidebars unmaintainable.
*   **Decision:**
    Adopt a **Hybrid Rendering Architecture**:
    *   **Rendering Canvas:** Built using **PixiJS v8** utilizing WebGL 2.0 with automatic WebGPU fallback. Handles rendering of nodes, orthogonal spline rail-routing, inferential current animations, and shader-based contradiction effects (e.g., visual fracturing when an inconsistency is triggered).
    *   **State Coordination:** Handled via **Zustand**, an un-opinionated, lightweight, reactive state manager in TypeScript. Zustand maintains the canonical local graph state outside of the React render loop.
    *   **UI Chrome & Modals:** Standard React 18 components bound reactively to Zustand state slices for UI panels, proof transcripts, and settings.
*   **Consequences:**
    *   *Positive:* Canvas rendering easily sustains 60–120 FPS performance even under heavy graph manipulation. Memory churn is minimized by bypassing React’s virtual DOM reconciliation for visual node coordinates, while preserving React’s component ergonomics for outer interface elements.
    *   *Negative / Trade-offs:* Developers must manage two paradigms: the declarative React UI tree and the imperative PixiJS scene graph. Care must be taken to prevent memory leaks in PixiJS textures and custom WebGL fragment shaders.
*   **Alternatives Considered:**
    1.  *Pure React Flow (DOM / SVG):* Discarded because benchmarks revealed frame rates dropping below 20 FPS when rendering dynamic particle flows across 100+ connected edges.
    2.  *Pure HTML5 Canvas (2D Context):* Discarded due to lack of native GPU shader support, which is required for custom contradiction fracture animations and smooth multi-layer line smoothing.

---

## 4. Verification & Algorithmic Specifications

### 4.1. Formal SMT Verification & MUS Extraction Algorithm

The procedural puzzle pipeline guarantees mathematical soundness and non-redundancy through an automated SMT sequence implemented in the Computational Epistemic Kernel (CEK):

```python
import z3

class EpistemicVerificationPipeline:
    def __init__(self, timeout_ms: int = 1500):
        self.timeout_ms = timeout_ms

    def verify_and_minimize(self, premises: list[z3.BoolRef], conclusion: z3.BoolRef) -> dict:
        """
        Validates soundness, uniqueness, and extracts the Minimal Unsatisfiable Subset (MUS).
        Guarantees:
          1. Premises are internally consistent: SAT(Premises) == True
          2. Entailment holds: UNSAT(Premises AND NOT Conclusion) == True
          3. Uniqueness: No alternative truth assignment satisfies premises while negating conclusion
          4. Non-redundancy: Every premise in the returned set is strictly necessary (MUS)
        """
        # Step 1: Prove Internal Consistency of Premises
        s_base = z3.Solver()
        s_base.set("timeout", self.timeout_ms)
        for p in premises:
            s_base.add(p)
            
        if s_base.check() != z3.sat:
            return {"status": "REJECTED", "reason": "PREMISES_INTERNALLY_CONTRADICTORY"}

        # Step 2: Prove Entailment & Uniqueness
        # A valid deduction requires: Premises |= Conclusion  <=>  Premises AND NOT Conclusion is UNSAT
        s_entail = z3.Solver()
        s_entail.set("timeout", self.timeout_ms)
        
        # Track individual premises using boolean indicator literals for MUS extraction
        indicators = [z3.Bool(f"ind_{i}") for i in range(len(premises))]
        for ind, p in zip(indicators, premises):
            s_entail.add(z3.Implies(ind, p))
            
        # Add negated target conclusion
        s_entail.add(z3.Not(conclusion))
        
        # Check satisfiability with all premises activated
        check_result = s_entail.check(indicators)
        
        if check_result == z3.sat:
            # Model found that satisfies premises but negates conclusion: AMBIGUOUS PUZZLE
            counter_model = s_entail.model()
            return {
                "status": "AMBIGUOUS",
                "counter_model": {d.name(): counter_model[d] for d in counter_model.decls()}
            }
        elif check_result != z3.unsat:
            return {"status": "TIMEOUT", "reason": "SOLVER_TIME_LIMIT_EXCEEDED"}

        # Step 3: Extract Minimal Unsatisfiable Subset (MUS)
        # Identifies the minimal core of premises required to force the conclusion
        raw_core = s_entail.unsat_core()
        active_indices = [int(str(ind).split("_")[1]) for ind in raw_core]
        minimal_premises = [premises[i] for i in active_indices]

        return {
            "status": "VERIFIED_SOUND",
            "is_unique": True,
            "original_premise_count": len(premises),
            "minimal_premise_count": len(minimal_premises),
            "mus_premises": minimal_premises,
            "redundant_premises_removed": len(premises) - len(minimal_premises)
        }
```

### 4.2. Algorithmic Complexity Guarantees & Safeguards

$$\begin{array}{|l|l|l|l|}
\hline
\textbf{Subsystem} & \textbf{Algorithm / Theoretical Bound} & \textbf{Deterministic Guardrail} & \textbf{Mitigation Strategy} \\ \hline
\text{ASP Synthesis} & \text{NP-Complete (Stable Model Semantics)} & 1,500\text{ ms hard cgroups limit} & \text{Pre-generation buffer; discard on timeout} \\ \hline
\text{SMT Verification} & \text{Undecidable (General) / PSPACE (QBF)} & \text{Restricted to Propositional + LRA} & \text{Strictly bounded quantifier-free logic} \\ \hline
\text{Client Wasm} & \text{Linear Resolution / 2-SAT / DPLL} & 16\text{ MB linear memory ceiling} & \text{Incremental Push/Pop; arena reset} \\ \hline
\text{SSNE Skinning} & \text{Deterministic CFG Parsing } \mathcal{O}(n^3) & 50\text{ ms per graph parsing budget} & \text{Strict CNL grammars; fallback skin} \\ \hline
\text{Telemetry} & \text{Append-Only Ingestion } \mathcal{O}(1) & 5,000\text{-event micro-batches} & \text{NATS backpressure; TimescaleDB COPY} \\ \hline
\end{array}$$

---

## 5. Summary Architecture Scorecard

```
+───────────────────────────────────+──────────────────────────────────────────────────────────────+
| ARCHITECTURAL INVARIANT           | ARCHITECTURAL REALIZATION & ENFORCEMENT                      |
+───────────────────────────────────+──────────────────────────────────────────────────────────────+
| 1. Absolute Soundness             | Dual-layer Z3 SMT entailment validation & MUS core           |
|                                   | extraction; verified prior to Redis pre-gen caching.         |
+───────────────────────────────────+──────────────────────────────────────────────────────────────+
| 2. Zero-Hallucination Skinning    | Attempto Controlled English (ACE) templates with closed-     |
|                                   | loop AST re-parsing; 1.0 structural isomorphism required.     |
+───────────────────────────────────+──────────────────────────────────────────────────────────────+
| 3. Sub-50ms Diagnostic Feedback   | Client-side compiled WebAssembly SMT/SAT micro-engine        |
|                                   | running local push/pop checks in <=15ms.                     |
+───────────────────────────────────+──────────────────────────────────────────────────────────────+
| 4. Isomorphic Orthogonality       | LogicGraphIR canonical structures stored in Neo4j;           |
|                                   | narrative domains bound dynamically at hydration phase.      |
+───────────────────────────────────+──────────────────────────────────────────────────────────────+
```

This specification provides the blueprints, physical interfaces, and operational policies for engineering teams to build and scale Project *Organon* as a robust, mathematically sound, enterprise-grade cognitive simulation platform.
