#!/usr/bin/env python3
# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Filter Velero backups by age threshold."""

import json
import os
import sys
from datetime import datetime, timezone, timedelta

def main():
    backups_json = os.environ.get('BACKUPS_JSON', '[]')
    max_age_hours = int(os.environ.get('MAX_AGE_HOURS', '6'))
    
    try:
        backups = json.loads(backups_json)
    except json.JSONDecodeError:
        print(json.dumps({"backups": [], "error": "Invalid JSON input"}))
        sys.exit(0)
    
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=max_age_hours)
    
    valid_backups = []
    for backup in backups:
        status = backup.get('status', {})
        completion_ts = status.get('completionTimestamp')
        if not completion_ts:
            continue
        
        try:
            ts = datetime.fromisoformat(completion_ts.replace('Z', '+00:00'))
            if ts >= cutoff:
                valid_backups.append({
                    "name": backup.get('metadata', {}).get('name'),
                    "completionTimestamp": completion_ts,
                    "age_hours": round((now - ts).total_seconds() / 3600, 2)
                })
        except (ValueError, TypeError):
            continue
    
    valid_backups.sort(key=lambda x: x['completionTimestamp'], reverse=True)
    
    print(json.dumps({"backups": valid_backups}))

if __name__ == "__main__":
    main()
