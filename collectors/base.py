"""
Base evidence collector — handles output directory structure, IPE generation,
and common patterns for all collectors.
"""
import csv
import json
import os
import datetime


class EvidenceCollector:
    def __init__(self, system_name, output_root=None):
        self.system_name = system_name
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_timestamp = ts
        self.output_root = output_root or os.path.expanduser(
            f"~/Downloads/2026 SOC II/evidence/{system_name}/{ts}"
        )
        os.makedirs(self.output_root, exist_ok=True)
        self._ipe_records = []

    def save_csv(self, filename, rows, fieldnames=None):
        if not rows:
            return None
        if fieldnames is None:
            fieldnames = list(rows[0].keys())
        path = os.path.join(self.output_root, filename)
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(rows)
        return path

    def save_json(self, filename, data):
        path = os.path.join(self.output_root, filename)
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)
        return path

    def save_text(self, filename, text):
        path = os.path.join(self.output_root, filename)
        with open(path, "w") as f:
            f.write(text)
        return path

    def record_ipe(self, evidence_file, endpoint, params, row_count,
                   pagination=None, notes=None):
        record = {
            "timestamp": datetime.datetime.now().isoformat(),
            "system": self.system_name,
            "evidence_file": os.path.basename(evidence_file) if evidence_file else None,
            "endpoint": endpoint,
            "parameters": params,
            "row_count": row_count,
            "pagination": pagination,
            "notes": notes,
        }
        self._ipe_records.append(record)
        return record

    def save_ipe(self):
        if not self._ipe_records:
            return None
        path = os.path.join(self.output_root, "IPE_documentation.json")
        with open(path, "w") as f:
            json.dump({
                "ipe_documentation": {
                    "generated_at": datetime.datetime.now().isoformat(),
                    "system": self.system_name,
                    "purpose": "Integrity of Processing Evidence — proves completeness and accuracy of exported data",
                    "records": self._ipe_records,
                }
            }, f, indent=2, default=str)

        txt_path = os.path.join(self.output_root, "IPE_documentation.txt")
        with open(txt_path, "w") as f:
            f.write(f"IPE DOCUMENTATION — {self.system_name}\n")
            f.write(f"Generated: {datetime.datetime.now().isoformat()}\n")
            f.write("=" * 70 + "\n\n")
            for rec in self._ipe_records:
                f.write(f"Evidence File: {rec['evidence_file']}\n")
                f.write(f"  Timestamp:  {rec['timestamp']}\n")
                f.write(f"  Endpoint:   {rec['endpoint']}\n")
                f.write(f"  Parameters: {json.dumps(rec['parameters'], default=str)}\n")
                f.write(f"  Row Count:  {rec['row_count']}\n")
                if rec.get('pagination'):
                    f.write(f"  Pagination: {rec['pagination']}\n")
                if rec.get('notes'):
                    f.write(f"  Notes:      {rec['notes']}\n")
                f.write("\n")
        return path

    def summary(self):
        files = []
        for root, dirs, filenames in os.walk(self.output_root):
            for fn in filenames:
                full = os.path.join(root, fn)
                files.append({
                    "file": os.path.relpath(full, self.output_root),
                    "size_kb": round(os.path.getsize(full) / 1024, 1),
                })
        return {
            "system": self.system_name,
            "output_dir": self.output_root,
            "timestamp": self.run_timestamp,
            "files_generated": files,
            "ipe_records": len(self._ipe_records),
        }
