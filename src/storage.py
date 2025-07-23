"""
AI Support Agent - Data Storage System
File-based data persistence with JSON storage and backup management
"""

import json
import os
import shutil
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import asdict

from models import ConversationHistory, AnalyticsData, CacheEntry
from config import Config


class DataStorage:
    """
    Manages persistent storage of conversations, analytics, and cache data
    Provides backup, recovery, and data integrity features
    """
    
    def __init__(self, backup_enabled: bool = True):
        """
        Initialize storage system
        
        Args:
            backup_enabled: Whether to enable automatic backups
        """
        self.backup_enabled = backup_enabled
        
        # Ensure directories exist
        Config.ensure_directories()
        
        # Storage files
        self.conversations_file = Config.CONVERSATIONS_FILE
        self.analytics_file = Config.ANALYTICS_FILE
        self.cache_file = Config.CACHE_FILE
        
        # Backup directory
        self.backup_dir = Config.DATA_DIR / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        # Thread safety
        self._file_locks = {
            'conversations': threading.RLock(),
            'analytics': threading.RLock(),
            'cache': threading.RLock()
        }
        
        # Auto-save tracking
        self._pending_saves = {
            'conversations': False,
            'analytics': False,
            'cache': False
        }
        
        # Start background save thread if enabled
        if self.backup_enabled:
            self._start_auto_save_thread()
    
    def save_conversation(self, conversation: ConversationHistory) -> bool:
        """
        Save a conversation to storage
        
        Args:
            conversation: ConversationHistory object to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            with self._file_locks['conversations']:
                # Load existing conversations
                conversations = self.load_all_conversations()
                
                # Update or add conversation
                conversations[conversation.session_id] = asdict(conversation)
                
                # Save to file
                return self._save_json_file(self.conversations_file, conversations)
                
        except Exception as e:
            self._log_error(f"Failed to save conversation: {str(e)}")
            return False
    
    def load_conversation(self, session_id: str) -> Optional[ConversationHistory]:
        """
        Load a specific conversation
        
        Args:
            session_id: Session ID to load
            
        Returns:
            ConversationHistory object if found, None otherwise
        """
        try:
            conversations = self.load_all_conversations()
            
            if session_id in conversations:
                data = conversations[session_id]
                return ConversationHistory(**data)
            
            return None
            
        except Exception as e:
            self._log_error(f"Failed to load conversation {session_id}: {str(e)}")
            return None
    
    def load_all_conversations(self) -> Dict[str, Any]:
        """Load all conversations from storage"""
        try:
            with self._file_locks['conversations']:
                return self._load_json_file(self.conversations_file, {})
                
        except Exception as e:
            self._log_error(f"Failed to load conversations: {str(e)}")
            return {}
    
    def save_analytics(self, analytics_data: AnalyticsData) -> bool:
        """
        Save analytics data to storage
        
        Args:
            analytics_data: AnalyticsData object to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            with self._file_locks['analytics']:
                # Convert to dictionary and add timestamp
                data = asdict(analytics_data)
                data['last_updated'] = datetime.now().isoformat()
                
                return self._save_json_file(self.analytics_file, data)
                
        except Exception as e:
            self._log_error(f"Failed to save analytics: {str(e)}")
            return False
    
    def load_analytics(self) -> Optional[AnalyticsData]:
        """Load analytics data from storage"""
        try:
            with self._file_locks['analytics']:
                data = self._load_json_file(self.analytics_file, None)
                
                if data:
                    # Remove timestamp if present
                    data.pop('last_updated', None)
                    return AnalyticsData(**data)
                
                return None
                
        except Exception as e:
            self._log_error(f"Failed to load analytics: {str(e)}")
            return None
    
    def save_cache_data(self, cache_data: Dict[str, Any]) -> bool:
        """
        Save cache data to storage
        
        Args:
            cache_data: Cache data dictionary
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            with self._file_locks['cache']:
                # Add metadata
                cache_data['saved_at'] = datetime.now().isoformat()
                
                return self._save_json_file(self.cache_file, cache_data)
                
        except Exception as e:
            self._log_error(f"Failed to save cache data: {str(e)}")
            return False
    
    def load_cache_data(self) -> Dict[str, Any]:
        """Load cache data from storage"""
        try:
            with self._file_locks['cache']:
                return self._load_json_file(self.cache_file, {})
                
        except Exception as e:
            self._log_error(f"Failed to load cache data: {str(e)}")
            return {}
    
    def create_backup(self, backup_name: Optional[str] = None) -> str:
        """
        Create a backup of all data files
        
        Args:
            backup_name: Optional custom backup name
            
        Returns:
            Path to created backup directory
        """
        if not backup_name:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)
        
        # Backup data files
        files_to_backup = [
            ('conversations.json', self.conversations_file),
            ('analytics.json', self.analytics_file),
            ('cache.json', self.cache_file)
        ]
        
        backed_up_files = []
        
        for backup_filename, source_file in files_to_backup:
            if source_file.exists():
                try:
                    dest_path = backup_path / backup_filename
                    shutil.copy2(source_file, dest_path)
                    backed_up_files.append(backup_filename)
                except Exception as e:
                    self._log_error(f"Failed to backup {backup_filename}: {str(e)}")
        
        # Create backup metadata
        metadata = {
            'created_at': datetime.now().isoformat(),
            'files': backed_up_files,
            'backup_name': backup_name
        }
        
        metadata_file = backup_path / 'backup_metadata.json'
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        return str(backup_path)
    
    def restore_backup(self, backup_name: str) -> bool:
        """
        Restore data from a backup
        
        Args:
            backup_name: Name of backup to restore
            
        Returns:
            True if restored successfully, False otherwise
        """
        backup_path = self.backup_dir / backup_name
        
        if not backup_path.exists():
            self._log_error(f"Backup not found: {backup_name}")
            return False
        
        try:
            # Create current backup before restoring
            current_backup = self.create_backup("pre_restore_backup")
            
            # Restore files
            files_to_restore = [
                ('conversations.json', self.conversations_file),
                ('analytics.json', self.analytics_file),
                ('cache.json', self.cache_file)
            ]
            
            restored_files = []
            
            for backup_filename, dest_file in files_to_restore:
                backup_file = backup_path / backup_filename
                if backup_file.exists():
                    try:
                        shutil.copy2(backup_file, dest_file)
                        restored_files.append(backup_filename)
                    except Exception as e:
                        self._log_error(f"Failed to restore {backup_filename}: {str(e)}")
            
            self._log_info(f"Restored {len(restored_files)} files from backup {backup_name}")
            return len(restored_files) > 0
            
        except Exception as e:
            self._log_error(f"Failed to restore backup {backup_name}: {str(e)}")
            return False
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups"""
        backups = []
        
        try:
            for backup_dir in self.backup_dir.iterdir():
                if backup_dir.is_dir():
                    metadata_file = backup_dir / 'backup_metadata.json'
                    
                    if metadata_file.exists():
                        try:
                            with open(metadata_file, 'r', encoding='utf-8') as f:
                                metadata = json.load(f)
                            
                            metadata['path'] = str(backup_dir)
                            metadata['size_mb'] = self._get_directory_size(backup_dir) / (1024 * 1024)
                            backups.append(metadata)
                            
                        except Exception as e:
                            # Backup without proper metadata
                            backups.append({
                                'backup_name': backup_dir.name,
                                'created_at': datetime.fromtimestamp(backup_dir.stat().st_mtime).isoformat(),
                                'files': [],
                                'path': str(backup_dir),
                                'size_mb': self._get_directory_size(backup_dir) / (1024 * 1024),
                                'error': f"Metadata error: {str(e)}"
                            })
            
            # Sort by creation date (newest first)
            backups.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
        except Exception as e:
            self._log_error(f"Failed to list backups: {str(e)}")
        
        return backups
    
    def cleanup_old_backups(self, keep_days: int = 30, keep_count: int = 10) -> int:
        """
        Clean up old backups
        
        Args:
            keep_days: Keep backups newer than this many days
            keep_count: Keep at least this many recent backups
            
        Returns:
            Number of backups removed
        """
        try:
            backups = self.list_backups()
            cutoff_date = datetime.now() - timedelta(days=keep_days)
            
            # Separate backups to keep and remove
            to_keep = []
            to_remove = []
            
            for backup in backups:
                try:
                    backup_date = datetime.fromisoformat(backup['created_at'])
                    
                    if len(to_keep) < keep_count or backup_date > cutoff_date:
                        to_keep.append(backup)
                    else:
                        to_remove.append(backup)
                        
                except Exception:
                    # Keep backups with invalid dates
                    to_keep.append(backup)
            
            # Remove old backups
            removed_count = 0
            for backup in to_remove:
                try:
                    backup_path = Path(backup['path'])
                    if backup_path.exists():
                        shutil.rmtree(backup_path)
                        removed_count += 1
                        
                except Exception as e:
                    self._log_error(f"Failed to remove backup {backup['backup_name']}: {str(e)}")
            
            return removed_count
            
        except Exception as e:
            self._log_error(f"Failed to cleanup backups: {str(e)}")
            return 0
    
    def export_data(self, export_path: str, include_cache: bool = False) -> bool:
        """
        Export all data to a specified directory
        
        Args:
            export_path: Directory to export data to
            include_cache: Whether to include cache data
            
        Returns:
            True if exported successfully, False otherwise
        """
        try:
            export_dir = Path(export_path)
            export_dir.mkdir(parents=True, exist_ok=True)
            
            # Export conversations
            conversations = self.load_all_conversations()
            conversations_file = export_dir / 'conversations_export.json'
            with open(conversations_file, 'w', encoding='utf-8') as f:
                json.dump(conversations, f, indent=2, ensure_ascii=False)
            
            # Export analytics
            analytics_data = self._load_json_file(self.analytics_file, {})
            analytics_file = export_dir / 'analytics_export.json'
            with open(analytics_file, 'w', encoding='utf-8') as f:
                json.dump(analytics_data, f, indent=2)
            
            # Export cache if requested
            if include_cache:
                cache_data = self.load_cache_data()
                cache_file = export_dir / 'cache_export.json'
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, indent=2)
            
            # Create export metadata
            metadata = {
                'exported_at': datetime.now().isoformat(),
                'files_exported': ['conversations_export.json', 'analytics_export.json'],
                'include_cache': include_cache
            }
            
            if include_cache:
                metadata['files_exported'].append('cache_export.json')
            
            metadata_file = export_dir / 'export_metadata.json'
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            return True
            
        except Exception as e:
            self._log_error(f"Failed to export data: {str(e)}")
            return False
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        try:
            stats = {
                'conversations_file_size_mb': self._get_file_size(self.conversations_file) / (1024 * 1024),
                'analytics_file_size_mb': self._get_file_size(self.analytics_file) / (1024 * 1024),
                'cache_file_size_mb': self._get_file_size(self.cache_file) / (1024 * 1024),
                'total_data_size_mb': 0,
                'backup_count': len(self.list_backups()),
                'backup_total_size_mb': self._get_directory_size(self.backup_dir) / (1024 * 1024)
            }
            
            stats['total_data_size_mb'] = (
                stats['conversations_file_size_mb'] + 
                stats['analytics_file_size_mb'] + 
                stats['cache_file_size_mb']
            )
            
            # Add conversation count
            conversations = self.load_all_conversations()
            stats['conversation_count'] = len(conversations)
            
            # Add last modified times
            stats['last_modified'] = {
                'conversations': self._get_last_modified(self.conversations_file),
                'analytics': self._get_last_modified(self.analytics_file),
                'cache': self._get_last_modified(self.cache_file)
            }
            
            return stats
            
        except Exception as e:
            self._log_error(f"Failed to get storage stats: {str(e)}")
            return {}
    
    def _save_json_file(self, file_path: Path, data: Any) -> bool:
        """Save data to JSON file safely"""
        try:
            # Write to temporary file first
            temp_file = file_path.with_suffix('.tmp')
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            # Atomic move to final location
            shutil.move(str(temp_file), str(file_path))
            
            return True
            
        except Exception as e:
            # Clean up temp file if it exists
            temp_file = file_path.with_suffix('.tmp')
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except:
                    pass
            
            raise e
    
    def _load_json_file(self, file_path: Path, default: Any = None) -> Any:
        """Load data from JSON file safely"""
        if not file_path.exists():
            return default
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            self._log_error(f"JSON decode error in {file_path}: {str(e)}")
            
            # Try to load backup if available
            backup_file = file_path.with_suffix('.backup')
            if backup_file.exists():
                try:
                    with open(backup_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except:
                    pass
            
            return default
        except Exception as e:
            self._log_error(f"Failed to load {file_path}: {str(e)}")
            return default
    
    def _get_file_size(self, file_path: Path) -> int:
        """Get file size in bytes"""
        try:
            return file_path.stat().st_size if file_path.exists() else 0
        except:
            return 0
    
    def _get_directory_size(self, dir_path: Path) -> int:
        """Get total size of directory in bytes"""
        try:
            total = 0
            for file_path in dir_path.rglob('*'):
                if file_path.is_file():
                    total += file_path.stat().st_size
            return total
        except:
            return 0
    
    def _get_last_modified(self, file_path: Path) -> Optional[str]:
        """Get last modified time as ISO string"""
        try:
            if file_path.exists():
                timestamp = file_path.stat().st_mtime
                return datetime.fromtimestamp(timestamp).isoformat()
            return None
        except:
            return None
    
    def _start_auto_save_thread(self) -> None:
        """Start background auto-save thread"""
        def auto_save_worker():
            import time
            
            while True:
                try:
                    time.sleep(300)  # Auto-save every 5 minutes
                    
                    # Create periodic backup
                    if datetime.now().hour == 3:  # 3 AM daily backup
                        self.create_backup()
                        
                        # Cleanup old backups weekly (on Sundays)
                        if datetime.now().weekday() == 6:
                            self.cleanup_old_backups()
                            
                except Exception:
                    pass  # Ignore auto-save errors
        
        auto_save_thread = threading.Thread(
            target=auto_save_worker,
            daemon=True,
            name="AutoSave"
        )
        auto_save_thread.start()
    
    def _log_error(self, message: str) -> None:
        """Log error message"""
        timestamp = datetime.now().isoformat()
        error_msg = f"[{timestamp}] STORAGE ERROR: {message}"
        
        # Try to write to log file
        try:
            with open(Config.LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(error_msg + '\n')
        except:
            # If logging fails, print to console
            print(error_msg)
    
    def _log_info(self, message: str) -> None:
        """Log info message"""
        timestamp = datetime.now().isoformat()
        info_msg = f"[{timestamp}] STORAGE INFO: {message}"
        
        try:
            with open(Config.LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(info_msg + '\n')
        except:
            print(info_msg)