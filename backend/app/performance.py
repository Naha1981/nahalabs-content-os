from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from .storage import DB_PATH, _connect


def init_performance_db(path: Path = DB_PATH) -> None:
    with _connect(path) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS performance_observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            publishing_job_id INTEGER NOT NULL,
            production_job_id INTEGER NOT NULL,
            prospect_id INTEGER NOT NULL,
            platform TEXT NOT NULL,
            observed_at TEXT NOT NULL,
            published_url TEXT NOT NULL DEFAULT '',
            impressions INTEGER NOT NULL DEFAULT 0,
            views INTEGER NOT NULL DEFAULT 0,
            likes INTEGER NOT NULL DEFAULT 0,
            comments INTEGER NOT NULL DEFAULT 0,
            shares INTEGER NOT NULL DEFAULT 0,
            saves INTEGER NOT NULL DEFAULT 0,
            clicks INTEGER NOT NULL DEFAULT 0,
            leads INTEGER NOT NULL DEFAULT 0,
            conversions INTEGER NOT NULL DEFAULT 0,
            revenue REAL NOT NULL DEFAULT 0,
            notes TEXT NOT NULL DEFAULT '',
            source TEXT NOT NULL DEFAULT 'MANUAL',
            created_at TEXT NOT NULL
        )""")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_perf_prospect ON performance_observations(prospect_id, observed_at DESC)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_perf_publish ON performance_observations(publishing_job_id, observed_at DESC)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_perf_platform ON performance_observations(platform, observed_at DESC)")


def _rates(d: dict[str, Any]) -> dict[str, Any]:
    denom = d.get("impressions") or d.get("views") or 0
    engaged = sum(d.get(k, 0) or 0 for k in ("likes", "comments", "shares", "saves"))
    d["engagements"] = engaged
    d["engagement_rate"] = round(engaged / denom * 100, 2) if denom else 0.0
    d["click_rate"] = round((d.get("clicks", 0) or 0) / denom * 100, 2) if denom else 0.0
    d["lead_rate"] = round((d.get("leads", 0) or 0) / denom * 100, 2) if denom else 0.0
    d["conversion_rate"] = round((d.get("conversions", 0) or 0) / (d.get("leads", 0) or 1) * 100, 2) if d.get("leads") else 0.0
    return d


def record_observation(job: dict[str, Any], metrics: dict[str, Any], path: Path = DB_PATH) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    observed_at = metrics.get("observed_at") or now
    fields = {k: metrics.get(k, 0) for k in ("impressions", "views", "likes", "comments", "shares", "saves", "clicks", "leads", "conversions", "revenue")}
    with _connect(path) as conn:
        cur = conn.execute("""INSERT INTO performance_observations
            (publishing_job_id,production_job_id,prospect_id,platform,observed_at,published_url,impressions,views,likes,comments,shares,saves,clicks,leads,conversions,revenue,notes,source,created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (job["id"], job["production_job_id"], job["prospect_id"], job["platform"], observed_at,
             metrics.get("published_url") or job.get("published_url", ""),
             *[max(0, int(fields[k] or 0)) for k in ("impressions", "views", "likes", "comments", "shares", "saves", "clicks", "leads", "conversions")],
             max(0.0, float(fields["revenue"] or 0)), metrics.get("notes", ""), metrics.get("source", "MANUAL"), now))
        oid = cur.lastrowid
        row = conn.execute("SELECT * FROM performance_observations WHERE id=?", (oid,)).fetchone()
    return _rates(dict(row))


def list_observations(prospect_id: int, path: Path = DB_PATH, limit: int = 100) -> list[dict[str, Any]]:
    with _connect(path) as conn:
        rows = conn.execute("SELECT * FROM performance_observations WHERE prospect_id=? ORDER BY observed_at DESC, id DESC LIMIT ?", (prospect_id, limit)).fetchall()
    return [_rates(dict(r)) for r in rows]


def learning_summary(prospect_id: int | None = None, path: Path = DB_PATH) -> dict[str, Any]:
    where = "WHERE prospect_id=?" if prospect_id is not None else ""
    args = [prospect_id] if prospect_id is not None else []
    with _connect(path) as conn:
        rows = conn.execute(f"SELECT * FROM performance_observations {where} ORDER BY observed_at DESC", args).fetchall()
        obs = [_rates(dict(r)) for r in rows]
        platform_rows = conn.execute(f"""SELECT platform, COUNT(*) observations, SUM(views) views, SUM(impressions) impressions,
            SUM(likes) likes, SUM(comments) comments, SUM(shares) shares, SUM(saves) saves,
            SUM(clicks) clicks, SUM(leads) leads, SUM(conversions) conversions, SUM(revenue) revenue
            FROM performance_observations {where} GROUP BY platform ORDER BY views DESC""", args).fetchall()
        platform = [_rates(dict(r)) for r in platform_rows]
        top = sorted(obs, key=lambda x: (x.get("engagement_rate", 0), x.get("leads", 0), x.get("views", 0)), reverse=True)[:5]
    totals = {k: sum((o.get(k) or 0) for o in obs) for k in ("impressions", "views", "likes", "comments", "shares", "saves", "clicks", "leads", "conversions", "revenue")}
    return {"prospect_id": prospect_id, "observations": len(obs), "totals": _rates(totals), "by_platform": platform, "top_observations": top,
            "learning": _learning_text(obs, platform)}


def _learning_text(obs: list[dict[str, Any]], platform: list[dict[str, Any]]) -> list[str]:
    if not obs:
        return ["No performance observations yet. Publish content and record results to start the learning loop."]
    notes = []
    best = max(obs, key=lambda x: (x.get("engagement_rate", 0), x.get("leads", 0), x.get("views", 0)))
    notes.append(f"Best observed engagement rate: {best['engagement_rate']}% on {best['platform']} (observation #{best['id']}).")
    lead_obs = [x for x in obs if x.get("leads", 0) > 0]
    if lead_obs:
        best_lead = max(lead_obs, key=lambda x: (x.get("leads", 0), x.get("conversion_rate", 0)))
        notes.append(f"Lead-producing observation: {best_lead['leads']} lead(s) on {best_lead['platform']}; conversion rate {best_lead['conversion_rate']}%.")
    if len(platform) > 1:
        best_platform = max(platform, key=lambda x: (x.get("engagement_rate", 0), x.get("leads", 0)))
        notes.append(f"Platform signal: {best_platform['platform']} currently has the strongest combined engagement/lead signal in recorded data.")
    notes.append("These are observed signals, not causal claims; continue collecting observations before changing the content strategy.")
    return notes
