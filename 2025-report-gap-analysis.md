# 2025 SOC 2 Report vs. 2026 Evidence Gap Analysis

Comparison of the 2025 Baker Tilly SOC 2 Type II Final Report (period 10/1/2024–9/30/2025) against ESEC evidence collected for the 2026 audit (period 10/1/2025–9/30/2026).

Report: `~/Downloads/2025 Earnest SOC 2 Type II Final Report.pdf` (91 pages)

---

## Prior-Year Exceptions (Highest Scrutiny)

The 2025 report had 5 exceptions. Baker Tilly will look hardest at whether these are remediated.

### 1. LS.07 — Access Reviews (3 sub-exceptions)

| What failed | Auditor test |
|---|---|
| SLO Platform quarterly access review not performed for 1 of 2 quarters | Semi-annual privileged + quarterly non-privileged SLO reviews |
| SLO Platform access review not performed | SLO Platform privileged access review |
| Annual non-privileged School Hub, CASHI, MMAX reviews not performed | Annual non-privileged reviews for all 3 systems |

**ESEC tickets:** ESEC-181, ESEC-183 (user handling, Q4 2025 + Q2 2026)

**What the auditor will check this year:**
- Quarterly SLO privileged reviews (need BOTH quarters done)
- Semi-annual SLO non-privileged reviews
- Semi-annual School Hub/CASHI/MMAX privileged reviews
- Annual School Hub/CASHI/MMAX non-privileged reviews
- That unnecessary access was actually removed after review

**Risk:** Repeat finding = much worse than one-time exception.

### 2. LS.02 — Access Provisioning Modifications

1 of 2 modified users had no access change ticket created.

**ESEC ticket:** ESEC-171 (140 tickets with full lifecycle data)

**Key detail:** Auditor separates new users from modifications, and tests "transfer questionnaires." Modification tickets need documented manager approval BEFORE access was granted.

### 3. LS.04 — Termination Access Removal

1 of 17 terminated users had other system access not disabled within 45 business days.

**What the auditor tests (3 separate checks):**
- AD network disable within 1 business day (automated job)
- Application access removal via IT ticket within 45 days
- Automated job history confirming it ran on termination day

### 4. LS.15 — Data Transmission Admin Access

1 of 37 users with admin access to data transmission platforms wasn't limited to authorized personnel.

**ESEC tickets:** ESEC-201/202 (Files.com via Okta SCIM, 62 users)

**Key detail:** They'll inspect admin users specifically — job-title justification needed.

### 5. EL.03 — Incident Response Training

95 of 232 required employees with core security responsibilities didn't complete IRT.

**Action:** Security Awareness Training completion is probably fine. Incident Response Training for security-responsible employees is the specific failure point.

---

## Evidence Mismatches

### LS.08 — Database Access / CyberArk

The 2025 control describes:
- Okta-issued credentials valid 24 hours + Pritunl VPN required
- Oracle/SQL DBAs use "emergency IDs" via CyberArk with 2FA
- Emergency IDs reviewed by DBA manager, auto-changed within 18 hours

**Question:** Is CyberArk still in use? If the Oracle/SQL DBAs are gone post-AWS-migration, the system description needs updating. If CyberArk is still used, need configuration + emergency ID activation evidence.

**ESEC ticket:** ESEC-186 (DBA login recording)

### CO.02 — Audit Log Protection

Auditor inspects the "Technology Audit and Logging Standard" document, admin users, and group permissions.

**Our evidence:** CrowdStrike cloud-hosted logs (immutable SaaS — strong story). ESEC-219 reopened for Splunk user data.

**Gap:** Need the logging standard policy document itself, not just tool configs.

### IT.07 — CISP Patch Management Language

Auditor inspects the CISP for: identification of systems needing scans, prioritization of patches, timeliness of patching, verification process.

**Risk:** If the CISP still references Splunk or pre-migration tooling instead of CrowdStrike Spotlight + Keystone + Grype, that's a finding.

### CO.06/CO.07 — File Management Tools (Files.com)

Auditor inspects:
- CO.06: SSL encryption certificates and encryption configuration
- CO.07: Scheduled job schedules for data transmissions

**Gap:** We have Okta SCIM user provisioning evidence for Files.com, but may be missing encryption config and scheduled transfer job evidence.

---

## System Description Changes

### Infrastructure Migration (May 18, 2025)

Completed before our audit period. For 2026:
- All Earnest apps are AWS-only (no Navient data center split)
- Files.com is the sole data transmission tool (NEST gone for Earnest side)
- Cyxtera/Centersquare DR site may no longer apply if DR is AWS multi-AZ/multi-region
- ENCORE migrated to DMS (Navient Cloud AWS) on 11/4/2025

### Splunk to CrowdStrike (Jan 2026)

| Control | What it references | Our evidence |
|---|---|---|
| CO.01 | Security log monitoring system | CrowdStrike config + alerts |
| CO.02 | Audit log protection | CrowdStrike cloud-hosted (immutable) |
| LS.11 | Enterprise protection software auto-updates | CrowdStrike sensor/prevention policies |
| LS.10 | Technology Audit Logging Standard | Need to verify policy updated for CrowdStrike |

---

## Controls Missing ESEC Tickets

| Control | What auditor tests | Notes |
|---|---|---|
| CO.04 | Wireless monitoring for rogue connections | Physical security — may be Navient responsibility |
| CO.05 | Third-party security threat intel monitoring | Vendor bulletins, security dashboards |
| LS.13 | Inbound email scanning (viruses/spam/phishing) | Email security tool config |
| EL.08 | SOC contact info on company intranet | Simple — screenshot of intranet page |
| CM.04 | Segregation of incompatible transaction processing | CISP policy reference |
| CM.06 | Navient compliance review of changes | Navient-managed control |
| LS.09 | DB/OS admin access semi-annual reviews | May overlap LS.07 but tested separately |
| LS.10 | Technology Audit Logging Standard | Policy doc — check Confluence sweep |
| IT.05 | Vendor management reviews | Tiered vendor review documentation |

---

## Misunderstood Control Intent

### LS.12 — Network Security

The auditor doesn't just look at security groups. They inspect:
- Network diagram AND firewall config
- Network TSM (Topology/Security Model) document
- "Deny-by-default" configuration
- Firewall, switch, router access controls, DMZ, remote access segmentation

**Our evidence:** ESEC-191/195 has SG data. Need network diagram and Network TSM doc.

### CM.07 — Environment Segregation

Auditor inspects "environment settings" to verify pre-implementation and production are segregated.

**Our evidence:** ESEC-150-156 per-system VPC/resource data (3 accounts: prod/dev/staging). May also need to show deployment pipeline settings preventing dev→prod direct access.

### CM.08 — Production Deployment Separation of Duties

Auditor inspects "a list of individuals with the ability to migrate changes to production" to verify access is limited to a team separate from development.

**Our evidence:** GitHub PR separation of duties. But auditor is checking deployment pipeline access — who can deploy vs. who develops. These should be different groups.

---

## All Controls Tested (2025 Report Reference)

### Control Environment (CC1.1–CC1.5)
EL.01, EL.02, EL.03, EL.04, EL.05, EL.06, EL.09, EL.10, EL.11, EL.12, EL.13

### Communication & Information (CC2.1–CC2.3)
CO.09, EL.07, EL.08, EL.10, EL.14, EL.17, IT.01, IT.03, IT.04, LS.01

### Risk Assessment (CC3.1–CC3.4)
EL.15, EL.16, EL.17, EL.18, IT.02, IT.06, IT.09

### Monitoring Activities (CC4.1–CC4.2)
EL.10, EL.14, EL.15, EL.17, IT.02, IT.03, IT.05, IT.06, IT.09

### Control Activities (CC5.1–CC5.3)
EL.14, EL.15, EL.17, EL.18, IT.02, IT.03, IT.04, IT.06, LS.01

### Logical & Physical Access (CC6.1–CC6.8)
CO.01, CO.04, CO.05, CO.06, CO.07, CO.08, IT.06, IT.09, LS.01–LS.16, PS.01–PS.08

### System Operations (CC7.1–CC7.5)
CO.01, CO.03, CO.09, IT.06–IT.12, LS.11, LS.12

### Change Management (CC8.1)
CM.01–CM.09

### Risk Mitigation (CC9.1–CC9.2)
CO.03, CO.09, EL.07, EL.17, IT.02, IT.06
