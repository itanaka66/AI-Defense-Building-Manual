# English edition — conventions (keep consistent across all parts)

Workflow: `python3 en/split.py` → translate `en/ja/volN.prose.md` into `en/tr/volN.prose.md` (keep every ⟦Ck⟧ placeholder on its own line, in order; keep inline `code` verbatim) → `python3 en/assemble.py N` (checks placeholders, inline code, leftover Japanese; writes en/volN.md, code comments translated via en/comments.json).

Front matter:
  title: "AI Autonomous Cyber Defense System | Build Manual | Volume 1"   (中編 → Volume 2; " | " = line break on title page)
  subtitle: "Part N: <title>"
  author: "Isamu Tanaka"
  lang: en-US

Headings: # Introduction / ## About This Book / ## Downloading the Scripts / ## Volumes and Parts / ## Notation
  第N章　X → "Chapter N: X";  ## 1.1　X → "## 1.1 X"
Fixed phrases:
  **実行先：X** → **Run on: X**   (Proxmoxホスト（root@pve） → the Proxmox host (root@pve); security-core VM 220（root） → security-core VM 220 (root); LXC 103 内 → inside LXC 103)
  実行結果（例）： → Example output:
  構築時 → in the original build / at build time
  前編/中編 → Volume 1 / Volume 2;  第N部 → Part N
  はじめに → Introduction;  おわりに → Closing Notes;  第N部の完了状態 → State at the End of Part N
  不足情報メモ items not translated (internal).

Part titles:
1 Building the Defense Foundation and Monitoring with Wazuh
2 Safely Monitoring PostgreSQL Logs and Correlation Detection
3 Building the Alert-Storage Collector
4 Auditing the Collector and Developing a Hardened Version
5 Deploying the Hardened Collector to Production
6 Verifying Data Integrity and Auditing Operations
7 Finishing the Collector's Fault Tolerance
8 Building the Integrated Monitoring Platform
9 Recovering from a Collector Stop and Checking Operations
10 Handling a Disk Failure and Preparing the AI Defense Manager
11 Laying the Groundwork for the AI Defense Manager
12 Investigating the AI Analysis Service and Wazuh Integration
13 A Read-Only User for Wazuh Indexer
14 Building the Alert Relay API (Relay)
15 Passing the Relay Connection Details Safely to VM 230
16 Connecting Wazuh Alerts to AI Analysis
17 Running the AI Defense Manager as a Service and Its Startup Order
18 Keeping the Analysis History in SQLite
19 Minimizing the Information Passed to the LLM
20 Fixing Confidence Scores and Protecting Stored Data
21 Switching SSH on VM 230 to Public-Key Authentication
22 Checking the Relay and Its Connection Details
23 Investigating Indexer Permissions and the Audit Log
24 Finding Out Why the Audit Log Is Not Saved
25 Setting Where the Audit Log Is Saved
26 Not Recording Request Bodies in the Audit Log
27 Confirming That the Audit Log Is Saved
28 Checking the Collector and Why It Stopped
29 Restarting the Collector Without Missing Any Events
30 Keeping the Collector from Stopping for the Same Reason

Terms: 中継API → relay API; 監査ログ → audit log; 読み取り位置 → read position (offset); 状態ファイル → state file; 隠しディレクトリ → hidden directory; 秘密の情報 → secrets; 相関検知 → correlation detection; 棚卸し → inventory; 待ち受け → listen; 疎通 → connectivity
Notation line must include: (Only Japanese comments inside the code have been translated into English.)
comments.json also holds diagram-line translations (vol16 C0) — text diagrams are not programs
