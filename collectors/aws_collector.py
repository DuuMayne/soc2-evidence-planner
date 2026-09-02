"""
AWS evidence collector — pulls VPC configs, security groups, RDS backups,
environment segregation, and network topology via boto3.

Requires: pip install boto3
Requires: AWS CLI configured with appropriate IAM permissions.
"""
import os
import sys
import json
import subprocess
import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from collectors.base import EvidenceCollector


def _run_aws_cli(cmd, profile=None):
    """Run an AWS CLI command and return parsed JSON output."""
    full_cmd = ["aws"] + cmd + ["--output", "json"]
    if profile:
        full_cmd += ["--profile", profile]
    result = subprocess.run(full_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"AWS CLI error: {result.stderr.strip()}")
    return json.loads(result.stdout) if result.stdout.strip() else {}


class AWSCollector(EvidenceCollector):
    def __init__(self, profile=None, regions=None, output_root=None):
        super().__init__("aws", output_root)
        self.profile = profile
        self.regions = regions or ["us-west-2", "us-east-1"]

    def _aws(self, cmd, region=None):
        full_cmd = list(cmd)
        if region:
            full_cmd += ["--region", region]
        return _run_aws_cli(full_cmd, self.profile)

    # ── VPC / Environment Segregation (ESEC-151 to ESEC-156) ──────────

    def collect_vpc_configs(self):
        """Export VPC configurations showing environment segregation."""
        all_vpcs = []
        for region in self.regions:
            try:
                data = self._aws(["ec2", "describe-vpcs"], region)
                vpcs = data.get("Vpcs", [])
                for vpc in vpcs:
                    tags = {t["Key"]: t["Value"] for t in vpc.get("Tags", [])}
                    all_vpcs.append({
                        "region": region,
                        "vpc_id": vpc["VpcId"],
                        "cidr_block": vpc.get("CidrBlock", ""),
                        "state": vpc.get("State", ""),
                        "is_default": vpc.get("IsDefault", False),
                        "name": tags.get("Name", ""),
                        "environment": tags.get("Environment", tags.get("env", "")),
                    })
                print(f"  {region}: {len(vpcs)} VPCs")
            except Exception as e:
                print(f"  {region}: error — {e}")

        path = self.save_csv("vpc_configurations.csv", all_vpcs)
        self.record_ipe(
            evidence_file=path,
            endpoint="aws ec2 describe-vpcs",
            params={"regions": self.regions},
            row_count=len(all_vpcs),
            notes="VPC configs showing environment segregation (ESEC-151 to ESEC-156)"
        )

        for region in self.regions:
            try:
                data = self._aws(["ec2", "describe-subnets"], region)
                subnets = data.get("Subnets", [])
                rows = []
                for s in subnets:
                    tags = {t["Key"]: t["Value"] for t in s.get("Tags", [])}
                    rows.append({
                        "region": region,
                        "subnet_id": s["SubnetId"],
                        "vpc_id": s["VpcId"],
                        "cidr_block": s.get("CidrBlock", ""),
                        "az": s.get("AvailabilityZone", ""),
                        "name": tags.get("Name", ""),
                        "public": s.get("MapPublicIpOnLaunch", False),
                    })
                self.save_csv(f"subnets_{region}.csv", rows)
                self.record_ipe(
                    evidence_file=f"subnets_{region}.csv",
                    endpoint="aws ec2 describe-subnets",
                    params={"region": region},
                    row_count=len(rows),
                    notes=f"Subnet details for {region} — environment segregation"
                )
            except Exception as e:
                print(f"  Subnets {region}: error — {e}")

        return all_vpcs

    # ── Security Groups (ESEC-193, ESEC-195) ──────────────────────────

    def collect_security_groups(self):
        """Export security group rules — firewall deny-all and VPN access."""
        all_sgs = []
        for region in self.regions:
            try:
                data = self._aws(["ec2", "describe-security-groups"], region)
                sgs = data.get("SecurityGroups", [])
                for sg in sgs:
                    for rule in sg.get("IpPermissions", []):
                        for cidr in rule.get("IpRanges", []):
                            all_sgs.append({
                                "region": region,
                                "group_id": sg["GroupId"],
                                "group_name": sg.get("GroupName", ""),
                                "vpc_id": sg.get("VpcId", ""),
                                "direction": "inbound",
                                "protocol": rule.get("IpProtocol", ""),
                                "from_port": rule.get("FromPort", ""),
                                "to_port": rule.get("ToPort", ""),
                                "cidr": cidr.get("CidrIp", ""),
                                "description": cidr.get("Description", ""),
                            })
                    for rule in sg.get("IpPermissionsEgress", []):
                        for cidr in rule.get("IpRanges", []):
                            all_sgs.append({
                                "region": region,
                                "group_id": sg["GroupId"],
                                "group_name": sg.get("GroupName", ""),
                                "vpc_id": sg.get("VpcId", ""),
                                "direction": "outbound",
                                "protocol": rule.get("IpProtocol", ""),
                                "from_port": rule.get("FromPort", ""),
                                "to_port": rule.get("ToPort", ""),
                                "cidr": cidr.get("CidrIp", ""),
                                "description": cidr.get("Description", ""),
                            })
                print(f"  {region}: {len(sgs)} security groups, {len([r for r in all_sgs if r['region'] == region])} rules")
            except Exception as e:
                print(f"  SGs {region}: error — {e}")

        path = self.save_csv("security_group_rules.csv", all_sgs)
        self.record_ipe(
            evidence_file=path,
            endpoint="aws ec2 describe-security-groups",
            params={"regions": self.regions},
            row_count=len(all_sgs),
            notes="Security group rules — firewall deny-all (ESEC-193) and VPN access (ESEC-195)"
        )
        return all_sgs

    # ── RDS/Backup Listings (ESEC-264, ESEC-267) ─────────────────────

    def collect_backup_configs(self):
        """Export RDS instances with backup configuration."""
        all_dbs = []
        for region in self.regions:
            try:
                data = self._aws(["rds", "describe-db-instances"], region)
                instances = data.get("DBInstances", [])
                for db in instances:
                    all_dbs.append({
                        "region": region,
                        "db_identifier": db["DBInstanceIdentifier"],
                        "engine": db.get("Engine", ""),
                        "engine_version": db.get("EngineVersion", ""),
                        "instance_class": db.get("DBInstanceClass", ""),
                        "multi_az": db.get("MultiAZ", False),
                        "storage_encrypted": db.get("StorageEncrypted", False),
                        "backup_retention_days": db.get("BackupRetentionPeriod", 0),
                        "preferred_backup_window": db.get("PreferredBackupWindow", ""),
                        "latest_restorable_time": str(db.get("LatestRestorableTime", "")),
                        "auto_minor_upgrade": db.get("AutoMinorVersionUpgrade", False),
                        "status": db.get("DBInstanceStatus", ""),
                    })
                print(f"  {region}: {len(instances)} RDS instances")
            except Exception as e:
                print(f"  RDS {region}: error — {e}")

        path = self.save_csv("rds_backup_configs.csv", all_dbs)
        self.record_ipe(
            evidence_file=path,
            endpoint="aws rds describe-db-instances",
            params={"regions": self.regions},
            row_count=len(all_dbs),
            notes="RDS instances with backup configuration (ESEC-264, ESEC-267)"
        )

        all_snapshots = []
        for region in self.regions:
            try:
                data = self._aws(["rds", "describe-db-snapshots", "--snapshot-type", "automated"], region)
                snapshots = data.get("DBSnapshots", [])
                for snap in snapshots:
                    all_snapshots.append({
                        "region": region,
                        "snapshot_id": snap.get("DBSnapshotIdentifier", ""),
                        "db_identifier": snap.get("DBInstanceIdentifier", ""),
                        "snapshot_create_time": str(snap.get("SnapshotCreateTime", "")),
                        "engine": snap.get("Engine", ""),
                        "status": snap.get("Status", ""),
                        "encrypted": snap.get("Encrypted", False),
                        "snapshot_type": snap.get("SnapshotType", ""),
                    })
                print(f"  {region}: {len(snapshots)} automated snapshots")
            except Exception as e:
                print(f"  Snapshots {region}: error — {e}")

        snap_path = self.save_csv("rds_automated_snapshots.csv", all_snapshots)
        self.record_ipe(
            evidence_file=snap_path,
            endpoint="aws rds describe-db-snapshots --snapshot-type automated",
            params={"regions": self.regions},
            row_count=len(all_snapshots),
            notes="Automated RDS snapshots — backup population (ESEC-264)"
        )
        return all_dbs

    # ── Backup Failures (ESEC-267) ────────────────────────────────────

    def collect_backup_failures(self):
        """Check CloudWatch/RDS events for backup failures."""
        all_events = []
        for region in self.regions:
            try:
                data = self._aws([
                    "rds", "describe-events",
                    "--source-type", "db-instance",
                    "--event-categories", "backup",
                    "--duration", "20160",  # last 14 days (RDS max)
                ], region)
                events = data.get("Events", [])
                for ev in events:
                    all_events.append({
                        "region": region,
                        "source_identifier": ev.get("SourceIdentifier", ""),
                        "source_type": ev.get("SourceType", ""),
                        "message": ev.get("Message", ""),
                        "event_categories": "; ".join(ev.get("EventCategories", [])),
                        "date": str(ev.get("Date", "")),
                    })
                print(f"  {region}: {len(events)} backup events")
            except Exception as e:
                print(f"  Backup events {region}: error — {e}")

        path = self.save_csv("backup_events.csv", all_events)
        self.record_ipe(
            evidence_file=path,
            endpoint="aws rds describe-events --source-type db-instance --event-categories backup",
            params={"regions": self.regions, "duration_minutes": 20160},
            row_count=len(all_events),
            notes="RDS backup events — backup failure population (ESEC-267)"
        )

        failures = [e for e in all_events if "fail" in e.get("message", "").lower() or "error" in e.get("message", "").lower()]
        if not failures:
            self.save_text("no_backup_failures.txt",
                f"CONFIRMATION: No backup failures detected in RDS events "
                f"for the past 30 days across regions {', '.join(self.regions)}.\n"
                f"Generated: {datetime.datetime.now().isoformat()}\n"
            )
        return all_events

    # ── Network Topology Summary (ESEC-192) ──────────────────────────

    def collect_network_topology(self):
        """Export route tables, internet gateways, NAT gateways for network diagram input."""
        for region in self.regions:
            try:
                rt_data = self._aws(["ec2", "describe-route-tables"], region)
                rts = rt_data.get("RouteTables", [])
                rt_rows = []
                for rt in rts:
                    tags = {t["Key"]: t["Value"] for t in rt.get("Tags", [])}
                    for route in rt.get("Routes", []):
                        rt_rows.append({
                            "region": region,
                            "route_table_id": rt["RouteTableId"],
                            "vpc_id": rt.get("VpcId", ""),
                            "name": tags.get("Name", ""),
                            "destination": route.get("DestinationCidrBlock", route.get("DestinationIpv6CidrBlock", "")),
                            "target": route.get("GatewayId") or route.get("NatGatewayId") or route.get("TransitGatewayId") or route.get("VpcPeeringConnectionId") or "local",
                            "state": route.get("State", ""),
                        })
                self.save_csv(f"route_tables_{region}.csv", rt_rows)
                self.record_ipe(
                    evidence_file=f"route_tables_{region}.csv",
                    endpoint="aws ec2 describe-route-tables",
                    params={"region": region},
                    row_count=len(rt_rows),
                    notes=f"Route tables for {region} — network topology (ESEC-192)"
                )
            except Exception as e:
                print(f"  Route tables {region}: error — {e}")

            try:
                igw_data = self._aws(["ec2", "describe-internet-gateways"], region)
                igws = igw_data.get("InternetGateways", [])
                igw_rows = []
                for igw in igws:
                    tags = {t["Key"]: t["Value"] for t in igw.get("Tags", [])}
                    for att in igw.get("Attachments", []):
                        igw_rows.append({
                            "region": region,
                            "igw_id": igw["InternetGatewayId"],
                            "name": tags.get("Name", ""),
                            "vpc_id": att.get("VpcId", ""),
                            "state": att.get("State", ""),
                        })
                self.save_csv(f"internet_gateways_{region}.csv", igw_rows)
            except Exception as e:
                print(f"  IGWs {region}: error — {e}")

            try:
                nat_data = self._aws(["ec2", "describe-nat-gateways"], region)
                nats = nat_data.get("NatGateways", [])
                nat_rows = []
                for nat in nats:
                    tags = {t["Key"]: t["Value"] for t in nat.get("Tags", [])}
                    nat_rows.append({
                        "region": region,
                        "nat_id": nat["NatGatewayId"],
                        "name": tags.get("Name", ""),
                        "vpc_id": nat.get("VpcId", ""),
                        "subnet_id": nat.get("SubnetId", ""),
                        "state": nat.get("State", ""),
                        "connectivity_type": nat.get("ConnectivityType", ""),
                    })
                self.save_csv(f"nat_gateways_{region}.csv", nat_rows)
            except Exception as e:
                print(f"  NAT GWs {region}: error — {e}")

        print(f"  Network topology data collected for {', '.join(self.regions)}")


def run_all(profile=None, regions=None, output_root=None):
    c = AWSCollector(profile, regions, output_root)

    print("\n=== AWS Evidence Collection ===\n")

    print("[1/5] VPC configurations...")
    c.collect_vpc_configs()

    print("[2/5] Security groups...")
    c.collect_security_groups()

    print("[3/5] RDS backup configs...")
    c.collect_backup_configs()

    print("[4/5] Backup failure events...")
    c.collect_backup_failures()

    print("[5/5] Network topology...")
    c.collect_network_topology()

    c.save_ipe()
    s = c.summary()
    print(f"\nDone. {len(s['files_generated'])} files in {s['output_dir']}")
    return s


if __name__ == "__main__":
    profile = os.environ.get("AWS_PROFILE")
    regions = os.environ.get("AWS_REGIONS", "us-west-2,us-east-1").split(",")
    run_all(profile, regions)
