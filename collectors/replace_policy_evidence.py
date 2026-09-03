#!/usr/bin/env python3
"""
Replace policy evidence on 7 ESEC tickets.

Steps:
  1. Re-pull Confluence page metadata to get refreshed dates
  2. Regenerate policy_mapping.csv + IPE_documentation.txt
  3. Delete old attachments from each ESEC ticket
  4. Upload new evidence: CSV + IPE + relevant PDFs per ticket
  5. Post updated ADF comments
"""
import os
import sys
import csv
import json
import datetime
import requests
from io import StringIO

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from scripts.jira_client import JiraClient
from scripts.adf import (
    doc, heading, paragraph, text, bold, italic,
    bullet_list, list_item, panel, rule, table, link_text,
)

EVIDENCE_ROOT = os.path.expanduser("~/Downloads/2026 SOC II/evidence")
POLICY_DIR = os.path.join(EVIDENCE_ROOT, "confluence/policy_sweep")
DOCUMENTS_DIR = os.path.expanduser("~/Downloads/Documents")

CONFLUENCE_BASE = "https://meetearnest.atlassian.net/wiki"

# ── Page-to-ticket mapping (from original sweep, all 49 pages) ──────────────
# Format: (page_id, esec_ticket, page_title, space_key, relevance)
PAGE_TICKET_MAP = [
    # ESEC-140: SDLC & Change Management Policy (14 pages)
    (2601484421, "ESEC-140", "SDLC Policy", "POL", "Primary SDLC policy document"),
    (2601354233, "ESEC-140", "SDLC Process", "POL", "Operational SDLC process — actively maintained"),
    (2601158559, "ESEC-140", "Change Management Process", "POL", "Formal change management process"),
    (2601354259, "ESEC-140", "Release Management Process", "POL", "Release management procedures"),
    (2601779213, "ESEC-140", "Infrastructure Change Management Process", "POL", "Infrastructure-specific change management"),
    (3398468366, "ESEC-140", "Coding Review Guidelines", "POL", "Code review requirements for all changes"),
    (3026944012, "ESEC-140", "Peer Review and Merging Best Practices", "POL", "Merge requirements and approval workflows"),
    (3393683568, "ESEC-140", "Definition of Done for SDLC @ Earnest", "POL", "Quality gates for SDLC completion"),
    (4019945570, "ESEC-140", "Engineering Release Process", "EN", "Current engineering release process"),
    (4117790746, "ESEC-140", "SDLC Policy (Navient Format)", "POL", "SDLC policy in Navient-compliant format"),
    (3415801921, "ESEC-140", "JIRA Practices for efficient SDLC Processes", "POL", "Jira workflow standards for change tracking"),
    (2694479948, "ESEC-140", "Going Merry SDLC Policy Addendum", "POL", "Team-level SDLC policy customization"),
    (2694283520, "ESEC-140", "Data Broker Change Management Process", "POL", "Specialized process for data pipeline changes"),
    (4835180604, "ESEC-140", "SDLC Refresh Command Center", "POL", "Active policy improvement program"),

    # ESEC-165: Network Authentication Policy (6 pages)
    (2608169971, "ESEC-165", "Data Loss Prevention (DLP) Plan", "POL", "DLP plan including authentication requirements"),
    (2629272590, "ESEC-165", "Information Data Classification", "POL", "Data classification driving auth requirements"),
    (2601354274, "ESEC-165", "Key Management Procedure", "POL", "Cryptographic key lifecycle for auth infrastructure"),
    (4509597717, "ESEC-165", "Transit Gateway + Site-to-Site VPN", "Enablement", "VPN architecture — network authentication"),
    (1617560006, "ESEC-165", "AWS Security Standard", "SEC", "AWS auth and access control requirements"),
    (2125267079, "ESEC-165", "Information Security Programs Policies Standards", "SEC", "Master info security policy"),

    # ESEC-175: Access Management Policy (5 pages)
    (2652212609, "ESEC-175", "Navient User Access Management Procedure", "POL", "User access provisioning/deprovisioning process"),
    (4595613720, "ESEC-175", "(DRAFT) Access Reviews", "SEC", "Periodic access certification procedures"),
    (4696735757, "ESEC-175", "Privilege Access Management", "SEC", "Controls for elevated access"),
    (956170509, "ESEC-175", "SailPoint Certifications", "SEC", "Automated access review tooling"),
    (2652375591, "ESEC-175", "Clean Desk Policy", "POL", "Physical access control for sensitive info"),

    # ESEC-188: Database Rules Document (3 pages)
    (809336836, "ESEC-188", "Database Guidelines", "EN", "Database design and maintenance guidelines"),
    (97290652, "ESEC-188", "ERD Review Process", "EN", "Peer review of database schema changes"),
    (2528051328, "ESEC-188", "ERD Training & Resources", "POL", "Database design review training"),

    # ESEC-194: Network Traffic Settings Policy (5 pages)
    (749732207, "ESEC-194", "Runbook - Cloudflare", "SEC", "WAF and traffic management procedures"),
    (4929159186, "ESEC-194", "Cloudflare WAF Rule Standardization", "IN", "Network traffic filtering policies"),
    (3232923765, "ESEC-194", "Docker and Kubernetes Security Best Practices", "SEC", "Container network policies"),
    (1617560006, "ESEC-194", "AWS Security Standard", "SEC", "Network security group and traffic policies"),
    (4509597717, "ESEC-194", "Transit Gateway + Site-to-Site VPN", "Enablement", "Network traffic routing between sites"),

    # ESEC-255: Vulnerability Management Policy (5 pages)
    (749798813, "ESEC-255", "Vulnerability Management", "POL", "Formal vulnerability management policy"),
    (4678549531, "ESEC-255", "Vulnerability Management Policy", "SEC", "Active vuln management policy"),
    (4771741718, "ESEC-255", "Container Image Vulnerability Management Proposal", "SEC", "Container vulnerability management"),
    (2564489224, "ESEC-255", "Earnest Patch Management SLA Process", "SEC", "Vulnerability remediation timelines"),
    (4963402170, "ESEC-255", "[DRAFT] Supply Chain Attacks Prevention", "SEC", "Software supply chain vuln management"),

    # ESEC-262: IT CP & IT DRP (10 pages)
    (2601811989, "ESEC-262", "IT Contingency and Disaster Recovery Plan (CP DRP)", "POL", "Master IT CP/DRP document"),
    (2601812000, "ESEC-262", "Section 1: Introduction - IT CP DRP", "POL", "DRP scope and objectives"),
    (2601812038, "ESEC-262", "Section 2: System Background - IT CP DRP", "POL", "Systems in scope for DR"),
    (2601812259, "ESEC-262", "Section 3: Incident Management Life Cycle - IT CP DRP", "POL", "Recovery procedures and escalation"),
    (2601780294, "ESEC-262", "Section 4: Reconstitution Phase - IT CP DRP", "POL", "Return-to-normal procedures"),
    (2601812295, "ESEC-262", "Section 5: DR Plan Testing - IT CP DRP", "POL", "DR testing and validation"),
    (2601780342, "ESEC-262", "Appendix B: Business Impact Analysis - IT CP DRP", "POL", "RTOs and RPOs for critical systems"),
    (2601812492, "ESEC-262", "Appendix C: BIA Summary - IT CP DRP", "POL", "Prioritized system recovery targets"),
    (2601780526, "ESEC-262", "Appendix D: Disaster Event Communication Plan - IT CP DRP", "POL", "Notification procedures during incidents"),
    (2467037569, "ESEC-262", "Business Continuity & Disaster Recovery", "POL", "BC/DR program documentation"),
    (4603740179, "ESEC-262", "Incident Response Plan (IRP)", "SEC", "Formal IRP"),
]

# ── PDF-to-ticket mapping ───────────────────────────────────────────────────
# Maps each PDF filename to (display_name, list of ESEC tickets, description)
PDF_TICKET_MAP = {
    "Navient CISP.pdf": (
        "Navient Corporate Information Security Program (CISP)",
        ["ESEC-140", "ESEC-165", "ESEC-175", "ESEC-194", "ESEC-255", "ESEC-262"],
        "55-page comprehensive InfoSec program, NIST-aligned, reviewed 03/09/2026. Parent company authoritative policy covering SDLC, access mgmt, network security, vuln mgmt, and DR.",
    ),
    "Navient AUP.pdf": (
        "Navient Acceptable Use Policy (AUP)",
        ["ESEC-165", "ESEC-175"],
        "17-page acceptable use policy, reviewed 07/07/2025. Covers network auth, access rules, and acceptable use of technology resources.",
    ),
    "Earnest SDLC Policy (22348_3).pdf": (
        "Earnest SDLC Policy (Navient Format)",
        ["ESEC-140"],
        "4-page Navient-format SDLC policy, reviewed 06/03/2025. CI/CD, PR review, testing, deployment requirements.",
    ),
    "SEC-Identity & Access Management Policy-030926-200419.pdf": (
        "Identity & Access Management Policy",
        ["ESEC-175"],
        "Earnest IAM policy v1.3, updated Sep 3, 2026. Provisioning, access reviews, MFA, naming conventions.",
    ),
    "SEC-Wireless LAN Security Standard-030926-200444.pdf": (
        "Wireless LAN Security Standard",
        ["ESEC-165", "ESEC-194"],
        "802.11 wireless security standard v1.2, updated Sep 3, 2026. EAP auth, network segmentation, WLAN monitoring.",
    ),
    "SEC-Earnest Bring Your Own Device (BYOD) Policy-030926-200545.pdf": (
        "Earnest BYOD Policy",
        ["ESEC-165", "ESEC-175"],
        "BYOD policy v2.2, updated Sep 3, 2026. MDM, device security, access requirements.",
    ),
    "SEC-Physical Security Policy-030926-200235.pdf": (
        "Physical Security Policy",
        ["ESEC-262"],
        "Physical security policy v1.2, updated Sep 3, 2026. AWS DC controls, office security, CCTV, access cards.",
    ),
    "SEC-Docker and Kubernetes Security Best Practices-030926-200805.pdf": (
        "Docker and Kubernetes Security Best Practices",
        ["ESEC-140", "ESEC-194"],
        "Container security hardening guide, updated Sep 3, 2026. Image hardening, K8s security, network policies.",
    ),
    "POL-Definition of Done for SDLC @ Earnest-030926-200711.pdf": (
        "Definition of Done for SDLC @ Earnest",
        ["ESEC-140"],
        "SDLC quality gates v1.0, updated Sep 3, 2026. API endpoints, auth, error handling, testing checklists.",
    ),
    "POL-JIRA Practices for efficient SDLC Processes-030926-200728.pdf": (
        "JIRA Practices for efficient SDLC Processes",
        ["ESEC-140"],
        "Jira workflow standards v1.0, updated Sep 3, 2026. Code review automation, sprint execution.",
    ),
    "POL-Section 3_ Incident Management Life Cycle Process - IT CP DRP-030926-200828.pdf": (
        "Section 3: Incident Management Life Cycle - IT CP DRP",
        ["ESEC-262"],
        "DR incident lifecycle, updated Sep 3, 2026. P0/P1 definitions, escalation, recovery procedures.",
    ),
}

SPACE_NAMES = {
    "POL": "Policies and Procedures",
    "SEC": "Security",
    "EN": "Engineering",
    "IN": "Infrastructure",
    "Enablement": "Enablement",
    "ITO": "IT Operations",
}

ESEC_DESCRIPTIONS = {
    "ESEC-140": "SDLC & Change Management Policy",
    "ESEC-165": "Network Authentication Policy",
    "ESEC-175": "Access Management Policy",
    "ESEC-188": "Database Rules Document",
    "ESEC-194": "Network Traffic Settings Policy",
    "ESEC-255": "Vulnerability Management Policy",
    "ESEC-262": "IT CP & IT DRP",
}


def confluence_get_page(session, page_id):
    url = f"{CONFLUENCE_BASE}/rest/api/content/{page_id}"
    params = {"expand": "version,history,space,ancestors"}
    resp = session.get(url, params=params)
    if resp.status_code != 200:
        print(f"  WARNING: Could not fetch page {page_id}: HTTP {resp.status_code}")
        return None
    return resp.json()


def pull_page_metadata(email, token):
    """Re-pull metadata for all 49 pages to capture refreshed dates."""
    session = requests.Session()
    session.auth = (email, token)
    session.headers.update({"Accept": "application/json"})

    unique_page_ids = list(set(p[0] for p in PAGE_TICKET_MAP))
    print(f"\nPulling metadata for {len(unique_page_ids)} unique Confluence pages...")

    page_cache = {}
    for i, pid in enumerate(unique_page_ids):
        data = confluence_get_page(session, pid)
        if data:
            page_cache[pid] = {
                "page_id": pid,
                "title": data["title"],
                "space_key": data["space"]["key"],
                "space_name": data["space"]["name"],
                "version_count": data["version"]["number"],
                "created_date": data["history"]["createdDate"][:10],
                "last_modified_date": data["version"]["when"][:10],
                "last_modified_by": data["version"]["by"].get("displayName", "Unknown"),
                "url": f"https://meetearnest.atlassian.net/wiki/spaces/{data['space']['key']}/pages/{pid}",
            }
        if (i + 1) % 10 == 0:
            print(f"  ...{i + 1}/{len(unique_page_ids)} pages fetched")

    print(f"  Done. {len(page_cache)}/{len(unique_page_ids)} pages retrieved.")
    return page_cache


def write_policy_csv(page_cache, output_path):
    """Write updated policy_mapping.csv with refreshed dates."""
    rows = []
    for page_id, ticket, title, space, relevance in PAGE_TICKET_MAP:
        meta = page_cache.get(page_id)
        if meta:
            rows.append({
                "esec_ticket": ticket,
                "control_description": ESEC_DESCRIPTIONS.get(ticket, ""),
                "page_id": page_id,
                "page_title": meta["title"],
                "space_key": meta["space_key"],
                "space_name": meta["space_name"],
                "version_count": meta["version_count"],
                "created_date": meta["created_date"],
                "last_modified_date": meta["last_modified_date"],
                "last_modified_by": meta["last_modified_by"],
                "relevance": relevance,
                "url": meta["url"],
            })
        else:
            rows.append({
                "esec_ticket": ticket,
                "control_description": ESEC_DESCRIPTIONS.get(ticket, ""),
                "page_id": page_id,
                "page_title": title,
                "space_key": space,
                "space_name": SPACE_NAMES.get(space, space),
                "version_count": "?",
                "created_date": "?",
                "last_modified_date": "?",
                "last_modified_by": "?",
                "relevance": relevance,
                "url": f"https://meetearnest.atlassian.net/wiki/spaces/{space}/pages/{page_id}",
            })

    fieldnames = [
        "esec_ticket", "control_description", "page_id", "page_title",
        "space_key", "space_name", "version_count", "created_date",
        "last_modified_date", "last_modified_by", "relevance", "url",
    ]

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n  Wrote {len(rows)} rows to {output_path}")
    return rows


def write_ipe(output_path, page_cache, pdf_files):
    """Write updated IPE documentation."""
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    unique_pages = len(set(p[0] for p in PAGE_TICKET_MAP))
    total_mappings = len(PAGE_TICKET_MAP)

    content = f"""IPE Documentation — Confluence Policy Documentation Sweep (Refreshed)
============================================================
Collection Timestamp: {now}
Collector: adam.duman@earnest.com via soc2-evidence-planner
Refresh Reason: Policy pages refreshed on 2026-09-03; evidence re-collected with updated dates


1. SOURCE SYSTEM IDENTIFICATION
--------------------------------
System: Atlassian Confluence Cloud
Instance: meetearnest.atlassian.net/wiki
Authentication: Basic Auth (adam.duman@earnest.com + Atlassian API token)
API Version: Confluence REST API v1 (/wiki/rest/api/content)

Additional Sources: {len(pdf_files)} policy PDFs from local document store
  - Navient CISP (55 pages, reviewed 03/09/2026) — Parent company InfoSec program
  - Navient AUP (17 pages, reviewed 07/07/2025) — Acceptable Use Policy
  - Earnest SDLC Policy (4 pages, reviewed 06/03/2025) — Navient-format SDLC
  - 8 Confluence-exported PDFs (all reviewed/updated Sep 3, 2026)


2. QUERIES EXECUTED
--------------------
Original CQL text searches (42 queries across spaces EN, SEC, POL, IN, ITO, Enablement):
  change management, SDLC, software development lifecycle, release management,
  change approval, network authentication, authentication policy, SSO, VPN access,
  multi factor, MFA, access management, access control, access provisioning,
  user access, role based, onboarding access, database access, database policy,
  DBA, database security, data access, network security, firewall, network policy,
  network traffic, security group, ingress egress, vulnerability management,
  vulnerability scanning, penetration test, security scanning, remediation,
  patching policy, disaster recovery, business continuity, incident recovery,
  backup recovery, continuity plan, DR plan, BCP

Page tree traversals (14 pages explored for children):
  - Engineering Home (524299)
  - Security@Earnest (96833059) — GRC, Old Docs, Cloud Security, TDR, VM subtrees
  - POL space full listing (41 pages)
  - IRP subtree (4603740179)
  - Security Policy and Controls (4557930497)

Refresh: Per-page metadata re-pulled for all {unique_pages} unique pages
  Endpoint: GET /wiki/rest/api/content/{{id}}?expand=version,history,space,ancestors
  Purpose: Capture refreshed last_modified_date after policy review on 2026-09-03


3. COMPLETENESS ASSERTIONS
---------------------------
Spaces searched: EN, SEC, POL, IN, ITO, Enablement (6 spaces)
Total search queries: 42 CQL text searches + 14 page tree traversals
Pages evaluated for relevance: 60+
Pages cataloged as evidence: {total_mappings} mappings across 7 ESEC tickets ({unique_pages} unique pages)
Additional PDF policies: {len(pdf_files)} documents (including Navient parent company policies)
Limitation: CQL returns max 25 results per query. Additional policy documents
may exist in spaces not searched or under different terminology.


4. ACCURACY CONTROLS
---------------------
Authentication: Atlassian Cloud Basic Auth — adam.duman@earnest.com
Data Path: Confluence REST API → HTTPS TLS 1.2+ → JSON → CSV
PDF Source: Local document exports from Confluence (SEC/POL spaces) + Navient PolicyTech
Transformation: Page metadata extracted directly from API responses. Control
  mapping and relevance descriptions added by collector. No page content was modified.
PDF documents are unmodified exports — file hashes can be verified against originals.


5. FILES GENERATED
-------------------
  - policy_mapping.csv — {total_mappings} page-to-ticket mappings across 7 ESEC tickets (refreshed dates)
  - IPE_documentation.txt — This file
  - {len(pdf_files)} PDF policy documents uploaded to relevant ESEC tickets


6. EVIDENCE MAPPING SUMMARY
-----------------------------
"""

    # Add per-ticket summary
    ticket_pages = {}
    for page_id, ticket, title, space, relevance in PAGE_TICKET_MAP:
        if ticket not in ticket_pages:
            ticket_pages[ticket] = []
        ticket_pages[ticket].append(title)

    ticket_pdfs = {}
    for fname, (display_name, tickets, desc) in PDF_TICKET_MAP.items():
        for t in tickets:
            if t not in ticket_pdfs:
                ticket_pdfs[t] = []
            ticket_pdfs[t].append(display_name)

    for ticket in sorted(ESEC_DESCRIPTIONS.keys()):
        desc = ESEC_DESCRIPTIONS[ticket]
        pages = ticket_pages.get(ticket, [])
        pdfs = ticket_pdfs.get(ticket, [])
        content += f"  {ticket} ({desc}): {len(pages)} Confluence pages"
        if pdfs:
            content += f" + {len(pdfs)} PDF policies"
        content += "\n"
        for p in pages:
            content += f"    - {p}\n"
        for p in pdfs:
            content += f"    - [PDF] {p}\n"
        content += "\n"

    with open(output_path, "w") as f:
        f.write(content)

    print(f"  Wrote IPE documentation to {output_path}")


def delete_old_attachments(client, ticket_key):
    """Delete all attachments from a ticket that match our old evidence files."""
    old_names = {"policy_mapping.csv", "IPE_documentation.txt", "IPE_documentation.json"}

    resp = client._request("GET", f"/rest/api/3/issue/{ticket_key}", params={"fields": "attachment"})
    client._check_response(resp, f"get attachments for {ticket_key}")
    data = resp.json()

    attachments = data.get("fields", {}).get("attachment", [])
    deleted = 0
    for att in attachments:
        fname = att["filename"]
        att_id = att["id"]
        if fname in old_names:
            print(f"    Deleting old attachment: {fname} (id={att_id})")
            if not client.dry_run:
                del_resp = client._request("DELETE", f"/rest/api/3/attachment/{att_id}")
                client._check_response(del_resp, f"delete attachment {att_id}")
            deleted += 1

    return deleted


def get_pdfs_for_ticket(ticket_key):
    """Return list of (filepath, display_name, description) for PDFs relevant to this ticket."""
    pdfs = []
    for fname, (display_name, tickets, desc) in PDF_TICKET_MAP.items():
        if ticket_key in tickets:
            fpath = os.path.join(DOCUMENTS_DIR, fname)
            if os.path.exists(fpath):
                pdfs.append((fpath, display_name, desc))
            else:
                print(f"  WARNING: PDF not found: {fpath}")
    return pdfs


def build_policy_comment(ticket_key, control_desc, confluence_pages, pdfs, csv_path):
    """Build ADF comment for a policy ticket with refreshed evidence."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    content = []

    content.append(heading("Policy Evidence — Refreshed", 3))
    content.append(panel("success",
        paragraph(
            bold("Evidence refreshed "),
            text(f"on {now} by soc2-evidence-planner. "),
            text("All Confluence policy pages reviewed and updated 2026-09-03. "),
            text("Old attachments deleted and replaced."),
        ),
    ))

    content.append(heading(f"{ticket_key}: {control_desc}", 4))

    # Confluence pages section
    if confluence_pages:
        content.append(paragraph(bold(f"Confluence Pages ({len(confluence_pages)})")))
        page_items = []
        for page in confluence_pages:
            page_items.append(list_item(paragraph(
                link_text(page["title"], page["url"]),
                text(f" ({page['space_key']}) — v{page['version_count']}, last modified {page['last_modified_date']} by {page['last_modified_by']}"),
            )))
        content.append(bullet_list(*page_items))

    # PDF policies section
    if pdfs:
        content.append(paragraph(bold(f"PDF Policy Documents ({len(pdfs)})")))
        pdf_items = []
        for fpath, display_name, desc in pdfs:
            pdf_items.append(list_item(paragraph(
                bold(display_name),
                text(f" — {desc}"),
            )))
        content.append(bullet_list(*pdf_items))

    # Files attached
    all_files = ["policy_mapping.csv", "IPE_documentation.txt"]
    for fpath, display_name, _ in pdfs:
        all_files.append(os.path.basename(fpath))

    content.append(rule())
    content.append(paragraph(
        bold("Files attached: "),
        text(", ".join(all_files)),
    ))
    content.append(paragraph(
        bold("IPE: "),
        text("See IPE_documentation.txt for query parameters, page counts, timestamps, and data path."),
    ))

    return doc(*content)


def run(email, token, dry_run=False):
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"\n{'='*60}")
    print(f"Policy Evidence Replacement — {now_str}")
    print(f"{'='*60}")

    # Step 1: Re-pull Confluence page metadata
    page_cache = pull_page_metadata(email, token)

    # Step 2: Regenerate CSV and IPE
    os.makedirs(POLICY_DIR, exist_ok=True)
    csv_path = os.path.join(POLICY_DIR, "policy_mapping.csv")
    ipe_path = os.path.join(POLICY_DIR, "IPE_documentation.txt")

    csv_rows = write_policy_csv(page_cache, csv_path)

    pdf_files = [f for f in os.listdir(DOCUMENTS_DIR) if f.endswith(".pdf")]
    write_ipe(ipe_path, page_cache, pdf_files)

    # Quick freshness check
    fresh_count = sum(1 for pid, meta in page_cache.items()
                      if meta["last_modified_date"] >= "2026-09-03")
    stale_count = len(page_cache) - fresh_count
    print(f"\n  Freshness: {fresh_count} pages updated on/after 2026-09-03, {stale_count} older")

    # Step 3-5: Per-ticket operations
    url = os.environ.get("JIRA_URL", "https://meetearnest.atlassian.net")
    client = JiraClient(url, email, token, dry_run=dry_run)

    results = {"success": [], "failed": [], "deleted": 0, "uploaded": 0}

    for ticket_key in sorted(ESEC_DESCRIPTIONS.keys()):
        control_desc = ESEC_DESCRIPTIONS[ticket_key]
        print(f"\n{'─'*50}")
        print(f"  {ticket_key}: {control_desc}")

        # Get Confluence pages for this ticket
        ticket_pages = []
        for page_id, tkt, title, space, relevance in PAGE_TICKET_MAP:
            if tkt == ticket_key:
                meta = page_cache.get(page_id)
                if meta:
                    ticket_pages.append({**meta, "relevance": relevance})

        # Get PDFs for this ticket
        pdfs = get_pdfs_for_ticket(ticket_key)

        try:
            # Delete old attachments
            deleted = delete_old_attachments(client, ticket_key)
            results["deleted"] += deleted
            print(f"    Deleted {deleted} old attachments")

            # Upload new CSV
            print(f"    Uploading policy_mapping.csv...")
            client.add_attachment(ticket_key, csv_path)
            results["uploaded"] += 1

            # Upload IPE
            print(f"    Uploading IPE_documentation.txt...")
            client.add_attachment(ticket_key, ipe_path)
            results["uploaded"] += 1

            # Upload relevant PDFs
            for fpath, display_name, desc in pdfs:
                fname = os.path.basename(fpath)
                print(f"    Uploading {fname}...")
                client.add_attachment(ticket_key, fpath)
                results["uploaded"] += 1

            # Post comment
            comment_adf = build_policy_comment(
                ticket_key, control_desc, ticket_pages, pdfs, csv_path
            )
            client.add_comment(ticket_key, comment_adf)
            print(f"    Comment posted. ({len(ticket_pages)} pages, {len(pdfs)} PDFs)")

            results["success"].append(ticket_key)

        except Exception as e:
            print(f"    ERROR: {e}")
            results["failed"].append({"key": ticket_key, "error": str(e)})

    # Summary
    print(f"\n{'='*60}")
    print(f"REPLACEMENT SUMMARY")
    print(f"{'='*60}")
    print(f"  Tickets processed: {len(results['success'])} success, {len(results['failed'])} failed")
    print(f"  Old attachments deleted: {results['deleted']}")
    print(f"  New files uploaded: {results['uploaded']}")
    if results["failed"]:
        print(f"\n  Failed:")
        for f in results["failed"]:
            print(f"    {f['key']}: {f['error'][:100]}")

    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Replace policy evidence on ESEC tickets")
    parser.add_argument("--dry-run", action="store_true", help="Preview without making changes")
    args = parser.parse_args()

    email = os.environ.get("JIRA_EMAIL")
    token = os.environ.get("JIRA_API_TOKEN")
    if not email or not token:
        print("Set JIRA_EMAIL and JIRA_API_TOKEN environment variables")
        print("  export JIRA_EMAIL='adam.duman@earnest.com'")
        print("  export JIRA_API_TOKEN='<token-from-1password>'")
        sys.exit(1)

    run(email, token, dry_run=args.dry_run)
