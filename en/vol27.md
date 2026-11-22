---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 2"
subtitle: "Part 27: Confirming That the Audit Log Is Saved"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 27 of Volume 2 of the "AI Autonomous Cyber Defense System Build Manual". In Part 25 we set the audit log's output destination, and in Part 26 we stopped request bodies from being recorded. Here we confirm the following **using reads only**, without changing settings.

1. The audit log index (`security-auditlog-YYYY.MM.dd`) has been created and events are being saved
2. The saved events contain no request bodies or authentication headers
3. The audit settings are stored in `.opendistro_security` and the design loads them again after a restart

The "values" of bodies and headers are not shown; only field names, counts, lengths and shapes are examined.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Everything is run on **security-core VM 220 (root)**.
- The index name `security-auditlog-2026.11.21` is from the day of the build. Replace it with the date in your environment.

# Chapter 1: Has the Destination Been Created?

## 1.1 The Startup Log

```bash
journalctl -u wazuh-indexer -b --no-pager | grep -Ei 'audit|sink|message routing|default storage' | tail -n 60
```

At build time nothing was shown. The absence of a log line does not by itself mean that the output destination was not created.

## 1.2 The Audit Log Index

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem 'https://127.0.0.1:9200/_cat/indices?format=json&h=index,health,status,docs.count,store.size' | python3 -c 'import json,sys; d=json.load(sys.stdin); rows=[x for x in d if "audit" in x.get("index","").lower()]; print("AUDIT_INDEX_COUNT:",len(rows)); [print(x) for x in rows]'
```

At build time `security-auditlog-2026.11.21` existed, holding 24 events and 103.7 KB. The audit log is being saved inside the Indexer.

## 1.3 Why It Is yellow

The index's state was `yellow`. Check the shards.

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem 'https://127.0.0.1:9200/_cat/shards/security-auditlog-2026.11.21?format=json&h=index,shard,prirep,state,node,unassigned.reason'
```

| Shard | State |
|---|---|
| Primary (p) | `STARTED` (node-1) |
| Replica (r) | `UNASSIGNED` (`INDEX_CREATED`) |

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem 'https://127.0.0.1:9200/_cluster/health?pretty'
```

There is one node, all 36 primary shards are running, and the only unassigned shard is this index's one replica. With only one node, there is nowhere to place the replica. This is not a save failure. The number of replicas is not changed, and the state is left `yellow` (author's notes, item 27-A).

# Chapter 2: What Is Being Saved

## 2.1 One Sample

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem 'https://127.0.0.1:9200/security-auditlog-2026.11.21/_search?size=1&filter_path=hits.hits._source' | python3 -c 'import json,sys; d=json.load(sys.stdin); h=d.get("hits",{}).get("hits",[]); print("SAMPLE_COUNT:",len(h)); s=h[0].get("_source",{}) if h else {}; print("TOP_LEVEL_FIELDS:",sorted(s)); print("BODY_FIELD_NAMES:",sorted(k for k in s if any(x in k.lower() for x in ("body","payload","request"))))'
```

This one event had no body field; it held information such as the REST method, path, source and user. For headers and URL parameters, look only at the names.

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem 'https://127.0.0.1:9200/security-auditlog-2026.11.21/_search?size=1&filter_path=hits.hits._source.audit_rest_request_headers,hits.hits._source.audit_rest_request_params' | python3 -c 'import json,sys; d=json.load(sys.stdin); h=d.get("hits",{}).get("hits",[]); s=h[0].get("_source",{}) if h else {}; headers=s.get("audit_rest_request_headers"); params=s.get("audit_rest_request_params"); print("HEADER_FIELD_TYPE:",type(headers).__name__); print("HEADER_NAMES:",sorted(headers.keys()) if isinstance(headers,dict) else "not a map"); print("PARAM_FIELD_TYPE:",type(params).__name__); print("PARAM_NAMES:",sorted(params.keys()) if isinstance(params,dict) else "not a map")'
```

The headers were only `Accept`, `Host` and `User-Agent`, and the only parameter was `filter_path`; there was no `Authorization` or `Cookie`.

## 2.2 All Events

Count body-like fields, authentication headers, header and parameter names, and categories.

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem 'https://127.0.0.1:9200/security-auditlog-2026.11.21/_search?size=100&filter_path=hits.hits._source' | python3 -c 'import json,sys,collections; d=json.load(sys.stdin); hs=d.get("hits",{}).get("hits",[]); body=[]; sensitive=[]; params=collections.Counter(); cats=collections.Counter(); headers=collections.Counter(); [cats.update([h.get("_source",{}).get("audit_category","UNKNOWN")]) for h in hs]; 
for h in hs:
 s=h.get("_source",{}); 
 for k in s:
  if any(x in k.lower() for x in ("request_body","requestbody","payload")): body.append(k)
 hd=s.get("audit_rest_request_headers",{}); 
 if isinstance(hd,dict):
  for k in hd:
   headers[k.lower()]+=1
   if k.lower() in ("authorization","proxy-authorization","cookie","set-cookie"): sensitive.append(k)
 p=s.get("audit_rest_request_params",{})
 if isinstance(p,dict): params.update(p.keys())
print("EVENTS_SCANNED:",len(hs)); print("BODY_FIELD_EVENT_COUNT:",len(body)); print("SENSITIVE_HEADER_EVENT_COUNT:",len(sensitive)); print("HEADER_NAME_COUNTS:",dict(headers)); print("PARAMETER_NAME_COUNTS:",dict(params)); print("AUDIT_CATEGORY_COUNTS:",dict(cats))'
```

At build time 86 events were examined. There were zero authentication headers, but **15 events had a body-like field**. Examine these 15 in detail.

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem 'https://127.0.0.1:9200/security-auditlog-2026.11.21/_search?size=100&filter_path=hits.hits._source' | python3 -c 'import json,sys; d=json.load(sys.stdin); hs=d.get("hits",{}).get("hits",[]); n=0
for h in hs:
 s=h.get("_source",{}); ks=[k for k in s if any(x in k.lower() for x in ("request_body","requestbody","payload"))]
 if ks:
  n+=1
  print("EVENT",n,"TIMESTAMP:",s.get("@timestamp"),"CATEGORY:",s.get("audit_category"),"MATCHING_FIELD_NAMES:",ks)
print("MATCHING_EVENTS:",n,"SCANNED:",len(hs))'
```

All 15 had the category `COMPLIANCE_INTERNAL_CONFIG_READ` (reading internal configuration), and the field was `audit_request_body`.

## 2.3 What audit_request_body Really Is

Without showing the values, examine only their shape.

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem 'https://127.0.0.1:9200/security-auditlog-2026.11.21/_search?size=100&filter_path=hits.hits._source' | python3 -c 'import json,sys; d=json.load(sys.stdin); hs=d.get("hits",{}).get("hits",[]); n=0
for h in hs:
 s=h.get("_source",{})
 if "audit_request_body" in s:
  v=s["audit_request_body"]; n+=1
  empty=(v is None or v=="" or v=={} or v==[])
  length=len(v) if isinstance(v,(str,dict,list)) else None
  print("EVENT",n,"TIMESTAMP:",s.get("@timestamp"),"TYPE:",type(v).__name__,"IS_NULL:",v is None,"IS_EMPTY:",empty,"LENGTH:",length)
print("BODY_FIELD_EVENTS:",n)'
```

All 15 were 25-character strings. Compare their contents with hashes.

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem 'https://127.0.0.1:9200/security-auditlog-2026.11.21/_search?size=100&filter_path=hits.hits._source' | python3 -c 'import json,sys,hashlib,collections; d=json.load(sys.stdin); vals=[h.get("_source",{}).get("audit_request_body") for h in d.get("hits",{}).get("hits",[]) if "audit_request_body" in h.get("_source",{})]; hashes=collections.Counter(hashlib.sha256(v.encode()).hexdigest() for v in vals if isinstance(v,str)); print("BODY_FIELD_COUNT:",len(vals)); print("UNIQUE_VALUE_COUNT:",len(hashes)); print("VALUE_FREQUENCIES:",sorted(hashes.values(),reverse=True)); print("ALL_VALUES_IDENTICAL:",len(hashes)==1 and len(vals)>0)'
```

All 15 had the same value. Examine the kinds of characters and the shape.

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem 'https://127.0.0.1:9200/security-auditlog-2026.11.21/_search?size=100&filter_path=hits.hits._source' | python3 -c 'import json,sys; d=json.load(sys.stdin); vals=[h["_source"]["audit_request_body"] for h in d.get("hits",{}).get("hits",[]) if "audit_request_body" in h.get("_source",{})]; v=vals[0] if vals else ""; print("LENGTH:",len(v)); print("ASCII_ONLY:",v.isascii()); print("ALPHANUMERIC_ONLY:",v.isalnum()); print("JSON_PARSEABLE:",end=" "); 
try: json.loads(v); print("yes")
except Exception: print("no")
print("HAS_WHITESPACE:",any(c.isspace() for c in v)); print("HAS_BRACES:",any(c in "{}[]" for c in v)); print("HAS_COLON:",":" in v); print("HAS_QUOTES:",any(c in chr(34)+chr(39) for c in v))'
```

It could be read as JSON. Look only at the key names and types.

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem 'https://127.0.0.1:9200/security-auditlog-2026.11.21/_search?size=100&filter_path=hits.hits._source' | python3 -c 'import json,sys; d=json.load(sys.stdin); vals=[h["_source"]["audit_request_body"] for h in d.get("hits",{}).get("hits",[]) if "audit_request_body" in h.get("_source",{})]; v=json.loads(vals[0]) if vals else None; print("PARSED_TYPE:",type(v).__name__); print("TOP_LEVEL_KEYS:",sorted(v.keys()) if isinstance(v,dict) else "not_object"); 
for k,x in (v.items() if isinstance(v,dict) else []): print("FIELD:",k,"TYPE:",type(x).__name__,"LENGTH:",len(x) if isinstance(x,(str,dict,list)) else "n/a","NESTED_KEYS:",sorted(x.keys()) if isinstance(x,dict) else "n/a")'
```

The shape was as follows (values masked).

```text
{"field_names":[...]}
```

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem 'https://127.0.0.1:9200/security-auditlog-2026.11.21/_search?size=100&filter_path=hits.hits._source' | python3 -c 'import json,sys; d=json.load(sys.stdin); vals=[json.loads(h["_source"]["audit_request_body"]) for h in d.get("hits",{}).get("hits",[]) if "audit_request_body" in h.get("_source",{})]; x=vals[0].get("field_names",[]) if vals else []; print("FIELD_NAMES_COUNT:",len(x)); print("ELEMENT_TYPES:",[type(v).__name__ for v in x]); print("ELEMENT_LENGTHS:",[len(v) if isinstance(v,(str,dict,list)) else None for v in x]); print("ALL_15_EVENTS_SAME_STRUCTURE:",all(v==vals[0] for v in vals))'
```

The `field_names` array contained a single five-character string, and all 15 had the same shape. This is considered to be not the body of an HTTP request but information about field names when the internal configuration was read.

## 2.4 Counts by Category

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem 'https://127.0.0.1:9200/security-auditlog-2026.11.21/_search?size=500&sort=@timestamp:desc&filter_path=hits.hits._source' | python3 -c 'import json,sys,collections; d=json.load(sys.stdin); hits=d.get("hits",{}).get("hits",[]); counts=collections.Counter(); body_counts=collections.Counter(); samples=collections.Counter(); 
for h in hits:
 s=h.get("_source",{}); c=s.get("audit_category","UNKNOWN"); counts[c]+=1
 if "audit_request_body" in s: body_counts[c]+=1
print("SCANNED_EVENTS:",len(hits)); print("CATEGORY_COUNTS:",dict(sorted(counts.items()))); print("BODY_FIELD_COUNTS_BY_CATEGORY:",dict(sorted(body_counts.items()))); print("BODY_FIELD_TOTAL:",sum(body_counts.values())); print("NON_COMPLIANCE_BODY_EVENTS:",sum(n for c,n in body_counts.items() if not c.startswith("COMPLIANCE_")))'
```

| Category | Count | With `audit_request_body` |
|---|---:|---:|
| `COMPLIANCE_INTERNAL_CONFIG_READ` | 15 | 15 |
| `COMPLIANCE_INTERNAL_CONFIG_WRITE` | 1 | 0 |
| `FAILED_LOGIN` | 8 | 0 |
| `INDEX_EVENT` | 62 | 0 |

Ordinary events (`FAILED_LOGIN`, `INDEX_EVENT`) have no body field.

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem 'https://127.0.0.1:9200/security-auditlog-2026.11.21/_search?size=500&sort=@timestamp:asc&filter_path=hits.hits._source.@timestamp,hits.hits._source.audit_category,hits.hits._source.audit_request_body' | python3 -c 'import json,sys,collections; d=json.load(sys.stdin); rows=[h["_source"] for h in d.get("hits",{}).get("hits",[]) if "audit_request_body" in h.get("_source",{})]; print("EVENT_COUNT:",len(rows)); print("FIRST_TIMESTAMP:",rows[0].get("@timestamp") if rows else "none"); print("LAST_TIMESTAMP:",rows[-1].get("@timestamp") if rows else "none"); print("CATEGORIES:",dict(collections.Counter(r.get("audit_category","UNKNOWN") for r in rows)))'
```

The 15 events were from 2026-11-21 08:27:45 to 08:56:05 (UTC).

# Chapter 3: Is the Design One in Which the Settings Persist?

## 3.1 The Current Settings

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem 'https://127.0.0.1:9200/_plugins/_security/api/audit' | python3 -c 'import json,sys; d=json.load(sys.stdin); c=d.get("config",{}); a=c.get("audit",{}); print("AUDIT_ENABLED:",c.get("enabled")); print("LOG_REQUEST_BODY:",a.get("log_request_body")); print("EXCLUDE_SENSITIVE_HEADERS:",a.get("exclude_sensitive_headers")); print("ENABLE_REST:",a.get("enable_rest")); print("ENABLE_TRANSPORT:",a.get("enable_transport")); print("DISABLED_REST_CATEGORIES:",a.get("disabled_rest_categories")); print("DISABLED_TRANSPORT_CATEGORIES:",a.get("disabled_transport_categories"))'
```

It still showed `LOG_REQUEST_BODY: False`.

## 3.2 The Configuration Document

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem 'https://127.0.0.1:9200/.opendistro_security/_doc/audit?filter_path=_index,_id,_version,_seq_no,_primary_term,found'
```

At build time it showed `found: true` and `_version: 2`. The change made by PATCH is saved as a document.

## 3.3 Loading at Startup

```bash
 /usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/plugins/opensearch-security/opensearch-security-2.19.6.0.jar:/usr/share/wazuh-indexer/lib/*' -p -c org.opensearch.security.configuration.ConfigurationRepository | grep -n -A45 -B12 'setupAuditConfigurationIfAny'
```

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/plugins/opensearch-security/opensearch-security-2.19.6.0.jar:/usr/share/wazuh-indexer/lib/*' -p -c org.opensearch.security.configuration.ConfigurationLoaderSecurity7 | grep -n -A55 -B15 'isAuditConfigDocPresentInIndex'
```

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/plugins/opensearch-security/opensearch-security-2.19.6.0.jar:/usr/share/wazuh-indexer/lib/*' -p -c 'org.opensearch.security.configuration.ConfigurationLoaderSecurity7$1' | grep -n -A35 -B15 -E 'AUDIT|isAuditConfigDocPresentInIndex|AtomicBoolean|set:|noData|success'
```

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/plugins/opensearch-security/opensearch-security-2.19.6.0.jar:/usr/share/wazuh-indexer/lib/*' -p -c org.opensearch.security.configuration.ConfigurationRepository | grep -n -A35 -B15 -E 'auditLog\.setConfig|AuditConfig|onChange|executeConfigurationInitialization'
```

1. The settings are saved in the document `audit` in `.opendistro_security`
2. At startup, `ConfigurationLoaderSecurity7` reads the document and sets a flag saying "the document exists"
3. `ConfigurationRepository` applies the settings read and enables reloading of the audit configuration (hot reload)

Because of this design, the settings changed with PATCH are used after a restart as well (this was not confirmed by actually restarting).

At build time we also searched the code for the class that calls `AuditLogImpl.setConfig()` when the settings change, but did not pin it down and stopped as it was of low necessity. Those steps are not included in this book.

# Chapter 4: Confirming with Aggregations

## 4.1 The Aggregation Does Not Work

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem -w '\nHTTP_STATUS:%{http_code}\n' 'https://127.0.0.1:9200/security-auditlog-*/_search?size=0&track_total_hits=true' | python3 -c 'import json,sys; s=sys.stdin.read(); body=s.split("\nHTTP_STATUS:")[0]; status=s.split("\nHTTP_STATUS:")[-1].strip() if "\nHTTP_STATUS:" in s else "unknown"; print("HTTP_STATUS:",status); d=json.loads(body); print("TOP_LEVEL_KEYS:",list(d.keys())); print("ERROR_TYPE:",d.get("error",{}).get("type") if isinstance(d.get("error"),dict) else None); print("ERROR_REASON:",d.get("error",{}).get("reason") if isinstance(d.get("error"),dict) else None); print("HITS_KEYS:",list(d.get("hits",{}).keys()))'
```

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem 'https://127.0.0.1:9200/_cat/indices/security-auditlog-*?format=json&h=index,docs.count,status' | python3 -c 'import json,sys; d=json.load(sys.stdin); print("INDEX_COUNT:",len(d)); [print("INDEX:",x.get("index"),"DOCS:",x.get("docs.count"),"STATUS:",x.get("status")) for x in d]'
```

The search returned `HTTP 200`, and the index had 88 events. However, aggregating by `audit_category` returned no results. Look at the error in the response.

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem -H 'Content-Type: application/json' 'https://127.0.0.1:9200/security-auditlog-2026.11.21/_search' -d '{"size":0,"track_total_hits":true,"aggs":{"categories":{"terms":{"field":"audit_category","size":30}}}}' | python3 -c 'import json,sys; d=json.load(sys.stdin); print("TOP_LEVEL_KEYS:",list(d)); print("ERROR:",d.get("error")); h=d.get("hits"); print("HITS_TYPE:",type(h).__name__); print("HITS_TOTAL:",h.get("total") if isinstance(h,dict) else None); print("AGGREGATIONS_TYPE:",type(d.get("aggregations")).__name__); print("AGGREGATION_KEYS:",list(d.get("aggregations",{})) if isinstance(d.get("aggregations"),dict) else None); print("SHARDS:",d.get("_shards"))'
```

`audit_category` is of type `text`, and `fielddata`, which the aggregation needs, is disabled, so the aggregation failed on every shard. Rather than enabling `fielddata` (which uses a lot of memory), check whether a `keyword`-type field exists.

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem 'https://127.0.0.1:9200/security-auditlog-2026.11.21/_mapping' | python3 -c 'import json,sys; d=json.load(sys.stdin); m=next(iter(d.values())).get("mappings",{}).get("properties",{}); print("audit_category:",m.get("audit_category")); print("audit_request_body:",m.get("audit_request_body")); print("audit_rest_request_headers:",m.get("audit_rest_request_headers"))'
```

`audit_category.keyword` and `audit_request_body.keyword` existed.

## 4.2 Aggregating with keyword

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem -H 'Content-Type: application/json' 'https://127.0.0.1:9200/security-auditlog-2026.11.21/_search' -d '{"size":0,"track_total_hits":true,"aggs":{"categories":{"terms":{"field":"audit_category.keyword","size":30}},"request_body_present":{"filter":{"exists":{"field":"audit_request_body"}}}}}' | python3 -c 'import json,sys; d=json.load(sys.stdin); print("ERROR_TYPE:",d.get("error",{}).get("type") if isinstance(d.get("error"),dict) else None); h=d.get("hits",{}); t=h.get("total"); print("TOTAL_EVENTS:",t.get("value") if isinstance(t,dict) else t); a=d.get("aggregations",{}); print("CATEGORIES:",{x["key"]:x["doc_count"] for x in a.get("categories",{}).get("buckets",[])}); print("REQUEST_BODY_PRESENT:",a.get("request_body_present",{}).get("doc_count"))'
```

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem -H 'Content-Type: application/json' 'https://127.0.0.1:9200/security-auditlog-2026.11.21/_search' -d '{"size":0,"aggs":{"categories":{"terms":{"field":"audit_category.keyword","size":30},"aggs":{"body_present":{"filter":{"exists":{"field":"audit_request_body"}}}}}}}' | python3 -c 'import json,sys; d=json.load(sys.stdin); print("ERROR_TYPE:",d.get("error",{}).get("type") if isinstance(d.get("error"),dict) else None); b=d.get("aggregations",{}).get("categories",{}).get("buckets",[]); [print("CATEGORY:",x["key"],"EVENTS:",x["doc_count"],"BODY_PRESENT:",x["body_present"]["doc_count"]) for x in b]'
```

| Category | Count | With a body field |
|---|---:|---:|
| `INDEX_EVENT` | 63 | 0 |
| `COMPLIANCE_INTERNAL_CONFIG_READ` | 17 | 17 |
| `FAILED_LOGIN` | 8 | 0 |
| `COMPLIANCE_INTERNAL_CONFIG_WRITE` | 1 | 0 |

## 4.3 The Shape of the 17

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem -H 'Content-Type: application/json' 'https://127.0.0.1:9200/security-auditlog-2026.11.21/_search' -d '{"size":20,"_source":["audit_category","audit_request_body"],"query":{"bool":{"filter":[{"term":{"audit_category.keyword":"COMPLIANCE_INTERNAL_CONFIG_READ"}},{"exists":{"field":"audit_request_body"}}]}}}' | python3 -c 'import json,sys; d=json.load(sys.stdin); h=d.get("hits",{}).get("hits",[]); print("SAMPLED_DOCS:",len(h)); import collections; stats=collections.Counter(); keys=collections.Counter(); shapes=collections.Counter(); 
for x in h:
 v=x.get("_source",{}).get("audit_request_body")
 if isinstance(v,str):
  stats[len(v)]+=1
  try:
   import json as j
   o=j.loads(v); shapes[type(o).__name__]+=1
   if isinstance(o,dict): keys[tuple(sorted(o.keys()))]+=1
  except Exception: shapes["invalid_json"]+=1
 else: shapes[type(v).__name__]+=1
print("LENGTH_COUNTS:",dict(stats)); print("JSON_SHAPES:",dict(shapes)); print("TOP_LEVEL_KEY_SETS:",{str(k):v for k,v in keys.items()})'
```

All 17 were 25-character JSON whose only key was `field_names`.

## 4.4 Matching Settings and Logs

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem 'https://127.0.0.1:9200/_plugins/_security/api/audit' | python3 -c 'import json,sys; d=json.load(sys.stdin); c=d.get("config",{}); a=c.get("audit",{}); m=c.get("compliance",{}); print("AUDIT_ENABLED:",c.get("enabled")); print("LOG_REQUEST_BODY:",a.get("log_request_body")); print("EXCLUDE_SENSITIVE_HEADERS:",a.get("exclude_sensitive_headers")); print("REST_ENABLED:",a.get("enable_rest")); print("TRANSPORT_ENABLED:",a.get("enable_transport")); print("COMPLIANCE_ENABLED:",m.get("enabled")); print("COMPLIANCE_READ_METADATA_ONLY:",m.get("read_metadata_only")); print("COMPLIANCE_WRITE_METADATA_ONLY:",m.get("write_metadata_only"))'
```

| Item | Value |
|---|---|
| Auditing | Enabled |
| REST and Transport auditing | Enabled |
| Recording request bodies | `false` |
| Excluding sensitive headers | `true` |
| Compliance | Enabled (metadata only for both reads and writes) |

# Closing Notes

In Part 27 we confirmed the following.

| Item | Result |
|---|---|
| Saving the audit log | Saved in `security-auditlog-YYYY.MM.dd` (89 events at build time) |
| Request bodies | Not recorded for ordinary events |
| The 17 events with `audit_request_body` | Only the fixed shape of internal configuration reads (`{"field_names":[...]}`) |
| Authentication headers | Not recorded |
| Settings | Saved in `.opendistro_security`; the design loads them at startup |
| Index state | `yellow` because there is only one node (replicas cannot be placed) |

Not every REST operation or every type of event was tested. In the next part, we check the Collector that sends Wazuh alerts to PostgreSQL.
