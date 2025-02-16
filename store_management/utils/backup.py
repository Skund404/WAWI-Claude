import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Optional


class DatabaseBackup:
    """Handler for database backups"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.backup_dir = db_path.parent / 'backups'
        self.backup_dir.mkdir(exist_ok=True)

    def create_backup(self, operation: str) -> Optional[Path]:
        """Create a backup before performing an operation"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = self.backup_dir / f"backup_{operation}_{timestamp}.db"

            conn = sqlite3.connect(self.db_path)
            backup_conn = sqlite3.connect(backup_path)

            conn.backup(backup_conn)

            conn.close()
            backup_conn.close()

            # Create backup metadata
            metadata = {
                'timestamp': timestamp,
                'operation': operation,
                'original_db': str(self.db_path),
                'backup_db': str(backup_path)
            }

            metadata_path = backup_path.with_suffix('.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)

            return backup_path

        except Exception as e:
            print(f"Backup error: {str(e)}")
            return None

    def restore_backup(self, backup_path: Path) -> bool:
        """Restore database from backup"""
        try:
            if not backup_path.exists():
                return False

            conn = sqlite3.connect(backup_path)
            restore_conn = sqlite3.connect(self.db_path)

            conn.backup(restore_conn)

            conn.close()
            restore_conn.close()

            return True

        except Exception as e:
            print(f"Restore error: {str(e)}")
            return False

    def list_backups(self) -> List[Dict[str, Any]]:
        """List available backups with metadata"""
        backups = []
        for metadata_file in self.backup_dir.glob('*.json'):
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                backups.append(metadata)
            except Exception:
                continue
        return sorted(backups, key=lambda x: x['timestamp'], reverse=True)

    def cleanup_old_backups(self, keep_days: int = 30) -> int:
        """Clean up backups older than specified days"""
        cleanup_date = datetime.now().timestamp() - (keep_days * 24 * 60 * 60)
        cleaned = 0

        for backup_file in self.backup_dir.glob('backup_*.db'):
            try:
                if backup_file.stat().st_mtime < cleanup_date:
                    backup_file.unlink()
                    metadata_file = backup_file.with_suffix('.json')
                    if metadata_file.exists():
                        metadata_file.unlink()
                    cleaned += 1
            except Exception:
                continue

        return cleaned