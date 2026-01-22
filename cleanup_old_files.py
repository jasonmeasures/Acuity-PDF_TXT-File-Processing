#!/usr/bin/env python3
"""
Cleanup script to remove old files from uploads and outputs directories.
Removes files older than specified days (default: 7 days).
"""

import os
import time
from pathlib import Path

def cleanup_directory(directory, days_old=7):
    """
    Remove files older than specified days from a directory
    
    Args:
        directory: Path to directory to clean
        days_old: Number of days old before file is deleted (default: 7)
    """
    if not os.path.exists(directory):
        print(f"Directory {directory} does not exist")
        return
    
    current_time = time.time()
    cutoff_time = current_time - (days_old * 24 * 60 * 60)  # Convert days to seconds
    
    removed_count = 0
    total_size_removed = 0
    
    for file_path in Path(directory).glob('*'):
        if file_path.is_file():
            file_stat = file_path.stat()
            
            # Check if file is older than cutoff
            if file_stat.st_mtime < cutoff_time:
                file_size = file_stat.st_size
                os.remove(file_path)
                removed_count += 1
                total_size_removed += file_size
                print(f"Removed: {file_path.name} ({file_size / 1024:.2f} KB)")
    
    total_mb = total_size_removed / (1024 * 1024)
    print(f"\nTotal removed from {directory}: {removed_count} files ({total_mb:.2f} MB)")
    
    return removed_count, total_size_removed

def main():
    """Main cleanup function"""
    print("=" * 60)
    print("Cleaning up old files from uploads and outputs directories")
    print("=" * 60)
    
    # Default: remove files older than 7 days
    days_old = 7
    
    print(f"\nRemoving files older than {days_old} days...\n")
    
    uploads_count = 0
    uploads_size = 0
    outputs_count = 0
    outputs_size = 0
    
    if os.path.exists('uploads'):
        print("Cleaning uploads/ directory:")
        uploads_count, uploads_size = cleanup_directory('uploads', days_old)
    
    if os.path.exists('outputs'):
        print("\nCleaning outputs/ directory:")
        outputs_count, outputs_size = cleanup_directory('outputs', days_old)
    
    total_files = uploads_count + outputs_count
    total_size = uploads_size + outputs_size
    total_mb = total_size / (1024 * 1024)
    
    print("\n" + "=" * 60)
    print(f"SUMMARY: Removed {total_files} files ({total_mb:.2f} MB)")
    print("=" * 60)

if __name__ == '__main__':
    main()




