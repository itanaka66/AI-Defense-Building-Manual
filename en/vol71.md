---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Part 71: Correlation, Orchestration and Defense Decision Agents"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 71 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual", and the last part of Volume 4. In Part 70 we built two agents, for log analysis and threat analysis. Here we build the following agents.

| Agent | Role |
|---|---|
| `IncidentCorrelationAgent` | relates multiple events by time, agent and classification; deterministic processing without an LLM |
| `SecurityAnalysisOrchestrator` | combines correlation and AI analysis (orchestrating the analysis) |
| `DefensePolicyAgent` | does not trust AI proposals as is; decides by server-side rules |

None of these agents performs defensive actions, IP blocking, notification or DB storage. Existing APIs, DB, settings and services are not changed either.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (`192.168.0.221`, root. When logged in as `aidefense`, become root with `sudo -i`)

# Chapter 1: The Event Correlation Agent

## 1.1 Available Fields

> **Run on: VM 230**

```bash
set -euo pipefail

ROOT=/opt/ai-defense-manager

echo "===== 1. WAZUH EVENT CONVERSION ====="
sed -n '1,280p' "$ROOT/app/services/wazuh_relay.py"

echo
echo "===== 2. SECURITY EVENT MODEL ====="
sed -n '1,240p' "$ROOT/app/schemas/security_event.py"

echo
echo "===== 3. WAZUH ANALYSIS REQUEST ====="
sed -n '1,220p' "$ROOT/app/schemas/wazuh.py"

echo
echo "===== 4. EXISTING TIME AND IP CORRELATION LOGIC ====="
grep -RInE 'observed_at|source_ip|destination_ip|agent_id|event_category|timeframe|correlat' \
  "$ROOT/app" --include='*.py' 2>/dev/null | head -200 || true

echo
echo "===== 5. PYTHON RUNTIME ====="
"$ROOT/venv/bin/python" --version

echo
echo "READ_ONLY=YES"
echo "FILES_MODIFIED=NO"
echo "DATABASE_CONTENT_READ=NO"
echo "SERVICE_RESTARTED=NO"
```

`SecurityEvent` has time, source IP, destination IP, agent ID and classification, but the current Wazuh conversion uses only `timestamp`, rule information, groups and `agent.id`, and does not pass IP addresses (because we narrowed it to seven fields in Part 48). **With the current Wazuh events alone, correlation by IP address is not possible.** We correlate using only the available fields.

| Item | Initial specification |
|---|---|
| Correlation key | same `agent_id` and same `event_category` |
| Time window | within 10 minutes of the first event |
| Minimum number of events | 2 |
| Time | time-zone-aware `observed_at` (normalized to UTC) |
| Correlation by IP | not used for now |
| Output | incident candidates, the event IDs they contain, the time range |

Events without `agent_id` are excluded so as not to relate them by mistake. Ten minutes is the value of this initial design.

## 1.2 Building

We create `app/agents/incident_correlation.py` and `tests/test_incident_correlation_agent.py` as new files.

> **Run on: VM 230**

```bash
set -euo pipefail

ROOT=/opt/ai-defense-manager
AGENT="$ROOT/app/agents/incident_correlation.py"
TEST="$ROOT/tests/test_incident_correlation_agent.py"

echo "===== VM230: INCIDENT CORRELATION AGENT CREATION ====="

# Prevent accidental overwrite.
if [ -e "$AGENT" ] || [ -e "$TEST" ]; then
    echo "ABORT: one or both target files already exist."
    exit 1
fi

cat > "$AGENT" <<'PY'
"""Deterministic, read-only security event correlation agent."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.schemas.analysis import AIAnalysisRequest


@dataclass(frozen=True, slots=True)
class IncidentCluster:
    """A candidate cluster of related security events."""

    agent_id: str
    event_category: str
    event_ids: tuple[UUID, ...]
    started_at: datetime
    ended_at: datetime


@dataclass(frozen=True, slots=True)
class IncidentCorrelationResult:
    """Correlation output; no defensive action is performed."""

    clusters: tuple[IncidentCluster, ...]
    uncorrelated_event_ids: tuple[UUID, ...]


class IncidentCorrelationError(ValueError):
    """Raised when the input cannot be correlated safely."""


class IncidentCorrelationAgent:
    """Group events by agent and category within a fixed time window."""

    def __init__(self, window: timedelta = timedelta(minutes=10)) -> None:
        if window <= timedelta(0):
            raise ValueError("correlation window must be positive")
        self._window = window

    def analyze(self, request: AIAnalysisRequest) -> IncidentCorrelationResult:
        events = request.events
        if not events:
            raise IncidentCorrelationError("request contains no security events")

        event_ids = [event.event_id for event in events]
        if len(event_ids) != len(set(event_ids)):
            raise IncidentCorrelationError("request contains duplicate event IDs")

        grouped: dict[tuple[str, str], list[tuple[datetime, UUID]]] = {}
        uncorrelated: list[UUID] = []

        for event in events:
            if event.agent_id is None or not str(event.agent_id).strip():
                uncorrelated.append(event.event_id)
                continue

            observed_at = event.observed_at
            if observed_at.tzinfo is None or observed_at.utcoffset() is None:
                raise IncidentCorrelationError(
                    "event timestamp must be timezone-aware"
                )

            key = (str(event.agent_id), str(event.event_category))
            grouped.setdefault(key, []).append(
                (observed_at.astimezone(timezone.utc), event.event_id)
            )

        clusters: list[IncidentCluster] = []

        for (agent_id, category), items in grouped.items():
            items.sort(key=lambda item: (item[0], str(item[1])))
            index = 0

            while index < len(items):
                start_time = items[index][0]
                end_limit = start_time + self._window
                bucket: list[tuple[datetime, UUID]] = []

                while index < len(items) and items[index][0] <= end_limit:
                    bucket.append(items[index])
                    index += 1

                if len(bucket) >= 2:
                    clusters.append(
                        IncidentCluster(
                            agent_id=agent_id,
                            event_category=category,
                            event_ids=tuple(item[1] for item in bucket),
                            started_at=bucket[0][0],
                            ended_at=bucket[-1][0],
                        )
                    )
                else:
                    uncorrelated.extend(item[1] for item in bucket)

        clusters.sort(
            key=lambda cluster: (
                cluster.started_at,
                cluster.agent_id,
                cluster.event_category,
                tuple(str(event_id) for event_id in cluster.event_ids),
            )
        )
        uncorrelated.sort(key=str)

        return IncidentCorrelationResult(
            clusters=tuple(clusters),
            uncorrelated_event_ids=tuple(uncorrelated),
        )
PY

cat > "$TEST" <<'PY'
"""Unit tests for deterministic incident correlation."""

import unittest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.agents.incident_correlation import (
    IncidentCorrelationAgent,
    IncidentCorrelationError,
)
from app.schemas.analysis import AIAnalysisRequest
from app.schemas.events import SecurityEvent


def make_event(
    *,
    minutes: int,
    agent_id: str | None = "agent-1",
    category: str = "authentication",
    observed_at: datetime | None = None,
) -> SecurityEvent:
    timestamp = observed_at or (
        datetime(2026, 11, 24, 12, 0, tzinfo=timezone.utc)
        + timedelta(minutes=minutes)
    )
    return SecurityEvent(
        event_id=uuid4(),
        source="wazuh",
        observed_at=timestamp,
        severity="low",
        agent_id=agent_id,
        event_category=category,
        event_summary="Synthetic correlation test event",
    )


def make_request(events: list[SecurityEvent]) -> AIAnalysisRequest:
    return AIAnalysisRequest(events=events)


class TestIncidentCorrelationAgent(unittest.TestCase):
    def setUp(self) -> None:
        self.agent = IncidentCorrelationAgent()

    def test_correlates_same_agent_and_category_within_ten_minutes(self):
        first = make_event(minutes=0)
        second = make_event(minutes=10)

        result = self.agent.analyze(make_request([first, second]))

        self.assertEqual(len(result.clusters), 1)
        cluster = result.clusters[0]
        self.assertEqual(cluster.agent_id, "agent-1")
        self.assertEqual(cluster.event_category, "authentication")
        self.assertEqual(set(cluster.event_ids), {first.event_id, second.event_id})
        self.assertEqual(len(result.uncorrelated_event_ids), 0)

    def test_does_not_chain_events_beyond_ten_minute_anchor_window(self):
        first = make_event(minutes=0)
        second = make_event(minutes=9)
        third = make_event(minutes=18)

        result = self.agent.analyze(make_request([first, second, third]))

        self.assertEqual(len(result.clusters), 1)
        self.assertEqual(
            set(result.clusters[0].event_ids),
            {first.event_id, second.event_id},
        )
        self.assertEqual(result.uncorrelated_event_ids, (third.event_id,))

    def test_does_not_correlate_different_agents_or_categories(self):
        events = [
            make_event(minutes=0, agent_id="agent-1", category="authentication"),
            make_event(minutes=1, agent_id="agent-2", category="authentication"),
            make_event(minutes=2, agent_id="agent-1", category="database"),
        ]

        result = self.agent.analyze(make_request(events))

        self.assertEqual(len(result.clusters), 0)
        self.assertEqual(
            set(result.uncorrelated_event_ids),
            {event.event_id for event in events},
        )

    def test_events_without_agent_id_remain_uncorrelated(self):
        first = make_event(minutes=0, agent_id=None)
        second = make_event(minutes=1, agent_id=None)

        result = self.agent.analyze(make_request([first, second]))

        self.assertEqual(len(result.clusters), 0)
        self.assertEqual(
            set(result.uncorrelated_event_ids),
            {first.event_id, second.event_id},
        )

    def test_normalizes_timezone_before_comparison(self):
        first = make_event(
            minutes=0,
            observed_at=datetime(2026, 11, 24, 12, 0, tzinfo=timezone.utc),
        )
        second = make_event(
            minutes=1,
            observed_at=datetime(
                2026, 11, 24, 21, 1,
                tzinfo=timezone(timedelta(hours=9)),
            ),
        )

        result = self.agent.analyze(make_request([first, second]))

        self.assertEqual(len(result.clusters), 1)
        self.assertEqual(
            result.clusters[0].ended_at - result.clusters[0].started_at,
            timedelta(minutes=1),
        )

    def test_rejects_duplicate_event_ids(self):
        event = make_event(minutes=0)
        duplicate = event.model_copy()

        with self.assertRaisesRegex(
            IncidentCorrelationError, "duplicate event IDs"
        ):
            self.agent.analyze(make_request([event, duplicate]))

    def test_rejects_non_positive_window(self):
        with self.assertRaises(ValueError):
            IncidentCorrelationAgent(window=timedelta(0))


if __name__ == "__main__":
    unittest.main()
PY

chown root:ai-defense "$AGENT"
chmod 0640 "$AGENT"
chown root:root "$TEST"
chmod 0640 "$TEST"

echo
echo "--- 1. Created files ---"
stat -c '%n | %U:%G | %a | %s bytes' "$AGENT" "$TEST"

echo
echo "--- 2. Run incident correlation tests ---"
cd "$ROOT"
PYTHONPATH="$ROOT" "$ROOT/venv/bin/python" -m unittest \
    discover -s "$ROOT/tests" \
    -p 'test_incident_correlation_agent.py' -v

echo
echo "--- 3. Run complete unit test suite ---"
PYTHONPATH="$ROOT" "$ROOT/venv/bin/python" -m unittest \
    discover -s "$ROOT/tests" \
    -p 'test_*.py' -v

echo
echo "INCIDENT_CORRELATION_TEST_RUN_COMPLETE"
```

The module name imported by the test file differed from the actual one, and the import failed.

```text
ModuleNotFoundError: No module named 'app.schemas.events'
```

## 1.3 Fixing the Test Import

`SecurityEvent` is in `app.schemas.security_event`.

```python
from app.schemas.security_event import SecurityEvent
```

We fix only the one import line of the test file. The agent itself, the API, the DB and the service are not touched.

> **Run on: VM 230**

```bash
set -euo pipefail

ROOT=/opt/ai-defense-manager
TEST="$ROOT/tests/test_incident_correlation_agent.py"

echo "===== VM230: FIX SECURITY EVENT TEST IMPORT ====="

echo
echo "--- 1. Verify current import ---"
grep -n 'app.schemas.*SecurityEvent' "$TEST"

echo
echo "--- 2. Apply the one-line import correction ---"
sed -i \
  's/from app\.schemas\.events import SecurityEvent/from app.schemas.security_event import SecurityEvent/' \
  "$TEST"

chown root:root "$TEST"
chmod 0640 "$TEST"

echo
echo "--- 3. Verify corrected import ---"
grep -n 'app.schemas.*SecurityEvent' "$TEST"

echo
echo "--- 4. Run incident correlation tests ---"
cd "$ROOT"
PYTHONPATH="$ROOT" "$ROOT/venv/bin/python" -m unittest \
  discover -s "$ROOT/tests" \
  -p 'test_incident_correlation_agent.py' -v

echo
echo "--- 5. Run complete unit test suite ---"
PYTHONPATH="$ROOT" "$ROOT/venv/bin/python" -m unittest \
  discover -s "$ROOT/tests" \
  -p 'test_*.py' -v

echo
echo "--- 6. Confirm file metadata ---"
stat -c '%n | %U:%G | %a | %s bytes' "$TEST"

echo
echo "INCIDENT_CORRELATION_IMPORT_FIX_COMPLETE"
```

| Agent | Tests |
|---|---:|
| `LogAnalysisAgent` | 2 passed |
| `ThreatAnalysisAgent` | 5 passed |
| `IncidentCorrelationAgent` | 7 passed |

All 14 passed. The specifications confirmed were: relating events of the same agent and classification within 10 minutes, normalizing time zones to UTC, not chaining beyond 10 minutes, excluding events without `agent_id`, rejecting duplicate event IDs, and not performing defensive actions.

# Chapter 2: The Analysis Orchestration Agent

## 2.1 Design

> **Run on: VM 230**

```bash
set -euo pipefail
ROOT=/opt/ai-defense-manager

echo "===== VM230: ORCHESTRATOR DESIGN DISCOVERY ====="

echo
echo "--- 1. Agent source files ---"
for f in \
  "$ROOT/app/agents/log_analysis.py" \
  "$ROOT/app/agents/threat_analysis.py" \
  "$ROOT/app/agents/incident_correlation.py"; do
  echo "### $f"
  sed -n '1,260p' "$f"
done

echo
echo "--- 2. Analysis schemas ---"
for f in \
  "$ROOT/app/schemas/analysis.py" \
  "$ROOT/app/schemas/analysis_proposal.py" \
  "$ROOT/app/schemas/security_event.py"; do
  echo "### $f"
  sed -n '1,280p' "$f"
done

echo
echo "--- 3. Existing orchestration / agent references ---"
grep -R -n -E \
  'Orchestrator|orchestrat|ThreatAnalysisAgent|IncidentCorrelationAgent|LogAnalysisAgent' \
  "$ROOT/app" --include='*.py' || true

echo
echo "--- 4. Existing tests inventory ---"
find "$ROOT/tests" -maxdepth 1 -type f -name 'test_*.py' -printf '%f\n' | sort

echo
echo "--- 5. API call paths (source only) ---"
sed -n '1,260p' "$ROOT/app/api/analysis.py"
sed -n '1,300p' "$ROOT/app/api/wazuh.py"

echo
echo "ORCHESTRATOR_DESIGN_DISCOVERY_COMPLETE"
```

`ThreatAnalysisAgent` calls `LogAnalysisAgent` internally. If the orchestration agent called both separately, the AI analysis would run twice. So we do the following.

1. Run the correlation analysis first
2. Call `ThreatAnalysisAgent` only once (`LogAnalysisAgent` runs inside it)
3. Return both results together
4. If either fails, propagate the exception; do not treat incomplete results as success
5. No defensive actions, IP blocking, notification or DB storage

## 2.2 Building and Testing

We create `app/agents/security_analysis_orchestrator.py` and `tests/test_security_analysis_orchestrator.py` as new files.

> **Run on: VM 230**

```bash
set -euo pipefail

ROOT=/opt/ai-defense-manager
AGENT="$ROOT/app/agents/security_analysis_orchestrator.py"
TEST="$ROOT/tests/test_security_analysis_orchestrator.py"

echo "===== VM230: SECURITY ANALYSIS ORCHESTRATOR CREATION ====="

# Do not overwrite existing files.
if [ -e "$AGENT" ] || [ -e "$TEST" ]; then
    echo "ABORT: one or both target files already exist."
    exit 1
fi

cat > "$AGENT" <<'PY'
"""Read-only orchestrator for security event analysis."""

from dataclasses import dataclass

from app.agents.incident_correlation import (
    IncidentCorrelationAgent,
    IncidentCorrelationResult,
)
from app.agents.threat_analysis import ThreatAnalysisAgent
from app.schemas.analysis import AIAnalysisRequest
from app.schemas.analysis_proposal import AIAnalysisProposal


@dataclass(frozen=True, slots=True)
class SecurityAnalysisResult:
    """Combined AI analysis and deterministic correlation results."""

    proposal: AIAnalysisProposal
    correlation: IncidentCorrelationResult


class SecurityAnalysisOrchestrator:
    """Coordinate correlation and threat analysis without taking action."""

    def __init__(
        self,
        correlation_agent: IncidentCorrelationAgent | None = None,
        threat_agent: ThreatAnalysisAgent | None = None,
    ) -> None:
        self._correlation_agent = (
            correlation_agent or IncidentCorrelationAgent()
        )
        self._threat_agent = threat_agent or ThreatAnalysisAgent()

    async def analyze(
        self,
        request: AIAnalysisRequest,
    ) -> SecurityAnalysisResult:
        # Correlation is deterministic and runs before the AI analysis.
        correlation = self._correlation_agent.analyze(request)

        # ThreatAnalysisAgent delegates to LogAnalysisAgent internally.
        # Call it once only to avoid duplicate AI analysis.
        proposal = await self._threat_agent.analyze(request)

        return SecurityAnalysisResult(
            proposal=proposal,
            correlation=correlation,
        )
PY

cat > "$TEST" <<'PY'
"""Unit tests for SecurityAnalysisOrchestrator."""

import unittest
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from app.agents.incident_correlation import (
    IncidentCorrelationResult,
)
from app.agents.security_analysis_orchestrator import (
    SecurityAnalysisOrchestrator,
)
from app.schemas.analysis import AIAnalysisRequest
from app.schemas.analysis_proposal import (
    AIAnalysisProposal,
    RecommendedAction,
)
from app.schemas.security_event import SecurityEvent


def make_request() -> AIAnalysisRequest:
    event = SecurityEvent(
        source="wazuh",
        severity="low",
        event_category="authentication",
        event_summary="Synthetic orchestrator test event",
    )
    return AIAnalysisRequest(events=[event])


def make_proposal(request: AIAnalysisRequest) -> AIAnalysisProposal:
    return AIAnalysisProposal(
        summary="Synthetic test analysis",
        severity="low",
        confidence=0.8,
        evidence_event_ids=[request.events[0].event_id],
        recommended_action=RecommendedAction.NO_ACTION,
        reasoning="Synthetic unit-test reasoning",
    )


class TestSecurityAnalysisOrchestrator(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.request = make_request()
        self.proposal = make_proposal(self.request)
        self.correlation_result = IncidentCorrelationResult(
            clusters=(),
            uncorrelated_event_ids=(self.request.events[0].event_id,),
        )

        self.correlation_agent = Mock()
        self.correlation_agent.analyze.return_value = self.correlation_result

        self.threat_agent = Mock()
        self.threat_agent.analyze = AsyncMock(return_value=self.proposal)

        self.orchestrator = SecurityAnalysisOrchestrator(
            correlation_agent=self.correlation_agent,
            threat_agent=self.threat_agent,
        )

    async def test_returns_combined_analysis_and_correlation(self):
        result = await self.orchestrator.analyze(self.request)

        self.assertIs(result.proposal, self.proposal)
        self.assertIs(result.correlation, self.correlation_result)
        self.correlation_agent.analyze.assert_called_once_with(self.request)
        self.threat_agent.analyze.assert_awaited_once_with(self.request)

    async def test_propagates_threat_analysis_failure(self):
        self.threat_agent.analyze.side_effect = RuntimeError(
            "synthetic threat analysis failure"
        )

        with self.assertRaisesRegex(
            RuntimeError, "synthetic threat analysis failure"
        ):
            await self.orchestrator.analyze(self.request)

        self.correlation_agent.analyze.assert_called_once_with(self.request)
        self.threat_agent.analyze.assert_awaited_once_with(self.request)

    async def test_propagates_correlation_failure_without_ai_call(self):
        self.correlation_agent.analyze.side_effect = ValueError(
            "synthetic correlation failure"
        )

        with self.assertRaisesRegex(
            ValueError, "synthetic correlation failure"
        ):
            await self.orchestrator.analyze(self.request)

        self.correlation_agent.analyze.assert_called_once_with(self.request)
        self.threat_agent.analyze.assert_not_awaited()

    async def test_calls_threat_agent_only_once(self):
        await self.orchestrator.analyze(self.request)

        self.threat_agent.analyze.assert_awaited_once()
        self.assertEqual(self.threat_agent.analyze.await_count, 1)


if __name__ == "__main__":
    unittest.main()
PY

chown root:ai-defense "$AGENT"
chmod 0640 "$AGENT"
chown root:root "$TEST"
chmod 0640 "$TEST"

echo
echo "--- 1. Created files ---"
stat -c '%n | %U:%G | %a | %s bytes' "$AGENT" "$TEST"

echo
echo "--- 2. Run orchestrator tests ---"
cd "$ROOT"
PYTHONPATH="$ROOT" "$ROOT/venv/bin/python" -m unittest \
    discover -s "$ROOT/tests" \
    -p 'test_security_analysis_orchestrator.py' -v

echo
echo "--- 3. Run complete unit test suite ---"
PYTHONPATH="$ROOT" "$ROOT/venv/bin/python" -m unittest \
    discover -s "$ROOT/tests" \
    -p 'test_*.py' -v

echo
echo "SECURITY_ANALYSIS_ORCHESTRATOR_TEST_RUN_COMPLETE"
```

| Test target | Result |
|---|---:|
| `IncidentCorrelationAgent` | 7 passed |
| `LogAnalysisAgent` | 2 passed |
| `ThreatAnalysisAgent` | 5 passed |
| `SecurityAnalysisOrchestrator` | 4 passed |
| Total | 18 passed, 0 failed |

We confirmed that the AI analysis runs only once, that when correlation fails the AI analysis is not run, and that when the AI analysis fails the exception is propagated.

# Chapter 3: The Defense Decision Agent

## 3.1 Existing Policy and Action Definitions

> **Run on: VM 230**

```bash
set -euo pipefail

ROOT=/opt/ai-defense-manager

echo "===== VM230: DEFENSE POLICY AGENT DISCOVERY ====="

echo
echo "--- 1. Policy directory inventory ---"
find "$ROOT/app/policies" -maxdepth 3 -type f -printf '%p | %s bytes\n' 2>/dev/null | sort || true

echo
echo "--- 2. Action and policy schemas ---"
for f in \
  "$ROOT/app/schemas/action.py" \
  "$ROOT/app/schemas/analysis_proposal.py" \
  "$ROOT/app/schemas/security_event.py"; do
  if [ -f "$f" ]; then
    echo "### $f"
    sed -n '1,300p' "$f"
  fi
done

echo
echo "--- 3. Policy and approval references ---"
grep -R -n -E \
  'ApprovalStatus|ActionProposal|TEMPORARY_BLOCK_IP|requires_human_approval|policy|approve|reject|ttl_seconds|target_ip' \
  "$ROOT/app" --include='*.py' || true

echo
echo "--- 4. Existing agent inventory ---"
find "$ROOT/app/agents" -maxdepth 1 -type f -name '*.py' -printf '%f\n' | sort

echo
echo "--- 5. Existing test inventory ---"
find "$ROOT/tests" -maxdepth 1 -type f -name 'test_*.py' -printf '%f\n' | sort

echo
echo "--- 6. Main application registration (source only) ---"
sed -n '1,280p' "$ROOT/app/main.py"

echo
echo "DEFENSE_POLICY_DISCOVERY_COMPLETE"
```

| Item | Existing rule |
|---|---|
| IP blocking target | global IPs only |
| TTL | 1–900 seconds |
| Evidence | two or more separate event IDs |
| Approval | required |
| Initial approval state | `PENDING` |
| AI's approval decision | the server-side policy takes precedence |

`app/policies/` was empty, and there was no `DefensePolicyAgent` yet.

## 3.2 Design

`DefensePolicyAgent` decides independently before an AI proposal is turned into an `ActionProposal`. Whatever the result, this agent itself performs no defensive actions.

| AI proposal | Decision |
|---|---|
| `NO_ACTION` | create no action |
| `MONITOR`, `HUMAN_REVIEW` | there is no corresponding existing `ActionType`, so err on the safe side and reject |
| `COLLECT_EVIDENCE`, `NOTIFY` | create a proposal |
| `TEMPORARY_BLOCK_IP` | check the IP, TTL, evidence IDs and correlation result, and always set `PENDING` |

IP blocking is further allowed only when all of the following hold.

- Two or more pieces of evidence are in the same correlation group (cluster)
- Severity is `high` or `critical`
- Confidence is `0.90` or higher

This is a fixed criterion on the defense policy side and cannot be changed by the AI's approval flag.

## 3.3 The Script to Build It

This script creates two files, `app/agents/defense_policy.py` and `tests/test_defense_policy_agent.py`, and also tests the edge conditions.

> **Run on: VM 230**

```bash
set -euo pipefail

ROOT=/opt/ai-defense-manager
test "$(id -u)" -eq 0
test -d "$ROOT/app/agents"
test -d "$ROOT/tests"
getent group ai-defense >/dev/null

cat > "$ROOT/app/agents/defense_policy.py" <<'PY'
from dataclasses import dataclass

from app.agents.incident_correlation import IncidentCorrelationResult
from app.schemas.action import ActionProposal, ActionType, ApprovalStatus
from app.schemas.analysis import AIAnalysisRequest
from app.schemas.analysis_proposal import AIAnalysisProposal, RecommendedAction


@dataclass(frozen=True, slots=True)
class DefensePolicyDecision:
    allowed: bool
    reason: str
    action_proposal: ActionProposal | None = None


class DefensePolicyAgent:
    """Apply deterministic server-side policy; never execute defensive actions."""

    BLOCK_MIN_CONFIDENCE = 0.90
    BLOCK_SEVERITIES = frozenset({"high", "critical"})

    def evaluate(
        self,
        proposal: AIAnalysisProposal,
        request: AIAnalysisRequest,
        correlation: IncidentCorrelationResult,
    ) -> DefensePolicyDecision:
        request_ids = [event.event_id for event in request.events]
        if not request_ids or len(request_ids) != len(set(request_ids)):
            return DefensePolicyDecision(False, "request events are empty or contain duplicate IDs")

        cluster_ids = [
            event_id
            for cluster in correlation.clusters
            for event_id in cluster.event_ids
        ]
        uncorrelated_ids = list(correlation.uncorrelated_event_ids)
        correlation_ids = cluster_ids + uncorrelated_ids

        if len(correlation_ids) != len(set(correlation_ids)):
            return DefensePolicyDecision(False, "correlation result contains duplicate event IDs")
        if not set(correlation_ids).issubset(set(request_ids)):
            return DefensePolicyDecision(False, "correlation result contains unknown event IDs")

        evidence_ids = proposal.evidence_event_ids
        if not evidence_ids or len(evidence_ids) != len(set(evidence_ids)):
            return DefensePolicyDecision(False, "evidence IDs are empty or contain duplicates")
        if not set(evidence_ids).issubset(set(request_ids)):
            return DefensePolicyDecision(False, "proposal references unknown evidence events")
        if not set(evidence_ids).issubset(set(correlation_ids)):
            return DefensePolicyDecision(False, "proposal evidence is absent from correlation result")

        action = proposal.recommended_action
        if action == RecommendedAction.NO_ACTION:
            return DefensePolicyDecision(True, "no action required")

        action_mapping = {
            RecommendedAction.NOTIFY: ActionType.NOTIFY,
            RecommendedAction.COLLECT_EVIDENCE: ActionType.COLLECT_EVIDENCE,
            RecommendedAction.TEMPORARY_BLOCK_IP: ActionType.TEMPORARY_BLOCK_IP,
        }
        action_type = action_mapping.get(action)
        if action_type is None:
            return DefensePolicyDecision(False, f"unsupported action type: {action.value}")

        if action == RecommendedAction.TEMPORARY_BLOCK_IP:
            if proposal.severity not in self.BLOCK_SEVERITIES:
                return DefensePolicyDecision(False, "IP blocking requires high or critical severity")
            if proposal.confidence < self.BLOCK_MIN_CONFIDENCE:
                return DefensePolicyDecision(False, "IP blocking requires confidence of at least 0.90")

            evidence_set = set(evidence_ids)
            matching_cluster = any(
                len(evidence_set.intersection(cluster.event_ids)) >= 2
                and evidence_set.issubset(set(cluster.event_ids))
                for cluster in correlation.clusters
            )
            if not matching_cluster:
                return DefensePolicyDecision(
                    False,
                    "IP blocking evidence must belong to one correlated incident",
                )

        try:
            action_proposal = ActionProposal(
                source_analysis_id=request.request_id,
                action_type=action_type,
                target_ip=proposal.target_ip,
                ttl_seconds=proposal.ttl_seconds,
                evidence_event_ids=evidence_ids,
                approval_status=ApprovalStatus.PENDING,
                requires_human_approval=True,
            )
        except (TypeError, ValueError) as exc:
            return DefensePolicyDecision(
                False,
                f"action proposal violates server constraints: {exc}",
            )

        return DefensePolicyDecision(
            True,
            "action proposal passed server policy",
            action_proposal,
        )
PY

cat > "$ROOT/tests/test_defense_policy_agent.py" <<'PY'
import unittest
from datetime import datetime, timezone
from uuid import uuid4

from pydantic import ValidationError

from app.agents.defense_policy import DefensePolicyAgent
from app.agents.incident_correlation import IncidentCluster, IncidentCorrelationResult
from app.schemas.analysis import AIAnalysisRequest
from app.schemas.analysis_proposal import AIAnalysisProposal, RecommendedAction
from app.schemas.security_event import SecurityEvent


class TestDefensePolicyAgent(unittest.TestCase):
    def setUp(self):
        self.agent = DefensePolicyAgent()
        self.events = [
            SecurityEvent(
                event_id=uuid4(),
                source="wazuh",
                observed_at=datetime(2026, 11, 24, 5, 0, tzinfo=timezone.utc),
                severity="high",
                agent_id="agent-1",
                event_category="authentication",
                event_summary=f"Failed login {i}",
            )
            for i in range(2)
        ]
        self.request = AIAnalysisRequest(events=self.events)
        self.ids = [event.event_id for event in self.events]
        self.cluster = IncidentCluster(
            agent_id="agent-1",
            event_category="authentication",
            event_ids=tuple(self.ids),
            started_at=self.events[0].observed_at,
            ended_at=self.events[1].observed_at,
        )
        self.correlation = IncidentCorrelationResult(
            clusters=(self.cluster,),
            uncorrelated_event_ids=(),
        )

    def proposal(self, action=RecommendedAction.NOTIFY, **overrides):
        values = {
            "summary": "Suspicious activity detected",
            "severity": "high",
            "confidence": 0.95,
            "evidence_event_ids": self.ids,
            "recommended_action": action,
            "reasoning": "Two related events were observed.",
        }
        values.update(overrides)
        return AIAnalysisProposal(**values)

    def test_notify_forces_human_approval_even_if_ai_says_false(self):
        result = self.agent.evaluate(
            self.proposal(requires_human_approval=False),
            self.request,
            self.correlation,
        )
        self.assertTrue(result.allowed)
        self.assertTrue(result.action_proposal.requires_human_approval)
        self.assertEqual(result.action_proposal.approval_status.value, "pending")

    def test_collect_evidence_is_supported(self):
        result = self.agent.evaluate(
            self.proposal(RecommendedAction.COLLECT_EVIDENCE),
            self.request,
            self.correlation,
        )
        self.assertTrue(result.allowed)
        self.assertEqual(result.action_proposal.action_type.value, "collect_evidence")

    def test_no_action_does_not_create_action(self):
        result = self.agent.evaluate(
            self.proposal(RecommendedAction.NO_ACTION),
            self.request,
            self.correlation,
        )
        self.assertTrue(result.allowed)
        self.assertIsNone(result.action_proposal)

    def test_monitor_and_human_review_are_rejected(self):
        for action in (RecommendedAction.MONITOR, RecommendedAction.HUMAN_REVIEW):
            with self.subTest(action=action):
                result = self.agent.evaluate(
                    self.proposal(action), self.request, self.correlation
                )
                self.assertFalse(result.allowed)
                self.assertIsNone(result.action_proposal)

    def test_private_ip_block_is_rejected_by_schema(self):
        with self.assertRaises(ValidationError):
            self.proposal(
                RecommendedAction.TEMPORARY_BLOCK_IP,
                target_ip="192.168.1.10",
                ttl_seconds=300,
            )

    def test_ttl_over_900_is_rejected_by_schema(self):
        with self.assertRaises(ValidationError):
            self.proposal(
                RecommendedAction.TEMPORARY_BLOCK_IP,
                target_ip="8.8.8.8",
                ttl_seconds=901,
            )

    def test_duplicate_evidence_is_rejected(self):
        result = self.agent.evaluate(
            self.proposal(evidence_event_ids=[self.ids[0], self.ids[0]]),
            self.request,
            self.correlation,
        )
        self.assertFalse(result.allowed)
        self.assertIn("duplicates", result.reason)

    def test_unknown_evidence_is_rejected(self):
        result = self.agent.evaluate(
            self.proposal(evidence_event_ids=[uuid4()]),
            self.request,
            self.correlation,
        )
        self.assertFalse(result.allowed)
        self.assertIn("unknown evidence", result.reason)

    def test_evidence_missing_from_correlation_is_rejected(self):
        incomplete = IncidentCorrelationResult(
            clusters=(),
            uncorrelated_event_ids=(self.ids[0],),
        )
        result = self.agent.evaluate(
            self.proposal(), self.request, incomplete
        )
        self.assertFalse(result.allowed)
        self.assertIn("absent from correlation", result.reason)

    def test_block_requires_high_or_critical_severity(self):
        result = self.agent.evaluate(
            self.proposal(
                RecommendedAction.TEMPORARY_BLOCK_IP,
                severity="medium",
                target_ip="8.8.8.8",
                ttl_seconds=300,
            ),
            self.request,
            self.correlation,
        )
        self.assertFalse(result.allowed)
        self.assertIn("severity", result.reason)

    def test_block_requires_minimum_confidence(self):
        result = self.agent.evaluate(
            self.proposal(
                RecommendedAction.TEMPORARY_BLOCK_IP,
                confidence=0.89,
                target_ip="8.8.8.8",
                ttl_seconds=300,
            ),
            self.request,
            self.correlation,
        )
        self.assertFalse(result.allowed)
        self.assertIn("confidence", result.reason)

    def test_block_requires_two_evidence_events_in_same_cluster(self):
        split = IncidentCorrelationResult(
            clusters=(
                IncidentCluster(
                    "agent-1",
                    "authentication",
                    (self.ids[0],),
                    self.events[0].observed_at,
                    self.events[0].observed_at,
                ),
            ),
            uncorrelated_event_ids=(self.ids[1],),
        )
        result = self.agent.evaluate(
            self.proposal(
                RecommendedAction.TEMPORARY_BLOCK_IP,
                target_ip="8.8.8.8",
                ttl_seconds=300,
            ),
            self.request,
            split,
        )
        self.assertFalse(result.allowed)
        self.assertIn("one correlated incident", result.reason)

    def test_valid_block_is_pending_and_human_approved(self):
        result = self.agent.evaluate(
            self.proposal(
                RecommendedAction.TEMPORARY_BLOCK_IP,
                target_ip="8.8.8.8",
                ttl_seconds=300,
                requires_human_approval=True,
            ),
            self.request,
            self.correlation,
        )
        self.assertTrue(result.allowed, result.reason)
        self.assertEqual(result.action_proposal.approval_status.value, "pending")
        self.assertTrue(result.action_proposal.requires_human_approval)

    def test_unknown_correlation_event_is_rejected(self):
        invalid = IncidentCorrelationResult(
            clusters=(),
            uncorrelated_event_ids=(uuid4(),),
        )
        result = self.agent.evaluate(
            self.proposal(), self.request, invalid
        )
        self.assertFalse(result.allowed)
        self.assertIn("correlation result contains unknown", result.reason)


if __name__ == "__main__":
    unittest.main()
PY

chown root:ai-defense "$ROOT/app/agents/defense_policy.py"
chmod 0640 "$ROOT/app/agents/defense_policy.py"
chown root:root "$ROOT/tests/test_defense_policy_agent.py"
chmod 0640 "$ROOT/tests/test_defense_policy_agent.py"

echo "===== VM230: DEFENSE POLICY AGENT TESTS ====="
PYTHONPATH="$ROOT" "$ROOT/venv/bin/python" -m unittest discover \
  -s "$ROOT/tests" -p 'test_defense_policy_agent.py' -v

echo
echo "===== VM230: FULL TEST SUITE ====="
PYTHONPATH="$ROOT" "$ROOT/venv/bin/python" -m unittest discover \
  -s "$ROOT/tests" -p 'test_*.py' -v

echo
echo "===== CREATED FILE METADATA ====="
stat -c '%n | %U:%G | %a | %s bytes' \
  "$ROOT/app/agents/defense_policy.py" \
  "$ROOT/tests/test_defense_policy_agent.py"
```

**The result of running this script is not within the build records received** (see the Missing Information Memo).

# Closing Notes

In Part 71 we built the event correlation and analysis orchestration agents and designed the defense decision agent.

| Agent | File | Tests |
|---|---|---|
| `LogAnalysisAgent` | `app/agents/log_analysis.py` | 2 passed |
| `ThreatAnalysisAgent` | `app/agents/threat_analysis.py` | 5 passed |
| `IncidentCorrelationAgent` | `app/agents/incident_correlation.py` | 7 passed |
| `SecurityAnalysisOrchestrator` | `app/agents/security_analysis_orchestrator.py` | 4 passed |
| `DefensePolicyAgent` | `app/agents/defense_policy.py` (up to the build script; the result is not in the records) | — |

None of the agents is connected to the API yet, and none performs defensive actions.

This is the end of the build records.
