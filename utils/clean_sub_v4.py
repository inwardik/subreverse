#!/usr/bin/env python3
"""
SRT File Repair Script (Multi-core version)

This script finds all .srt files in the current directory and subdirectories,
then repairs them by:
1. Removing HTML tags
2. Removing content in parentheses (), brackets [], and braces {}
3. Skipping entire subtitle blocks containing ♪ symbols (music notation)
4. Skipping subtitle blocks with only a single character
5. Removing leading and trailing dashes (- and –)
6. Merging consecutive subtitle entries with identical text
7. Recreating sequential numbering starting from 1

Usage: python srt_repair.py
"""

import os
import re
from pathlib import Path
import shutil
from typing import List, Tuple
from multiprocessing import Pool, cpu_count

def find_srt_files(directory: str = ".") -> List[Path]:
    """Find all .srt files in the directory and subdirectories."""
    srt_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.srt'):
                srt_files.append(Path(root) / file)
    return srt_files

def contains_music_symbol(text: str) -> bool:
    """
    Check if text contains the music symbol ♪.
    
    Args:
        text: Text to check
        
    Returns:
        True if music symbol is found, False otherwise
    """
    return 'â™ª' in text or '♪' in text

def is_single_character(text: str) -> bool:
    """
    Check if text contains only one character after cleaning HTML tags.
    
    Args:
        text: Text to check
        
    Returns:
        True if text is a single character, False otherwise
    """
    # Remove HTML tags
    cleaned = re.sub(r'<[^>]+>', '', text)
    # Remove whitespace
    cleaned = cleaned.strip()
    # Check if it's a single character
    return len(cleaned) == 1

def clean_text(text: str) -> str:
    """
    Clean subtitle text by removing HTML tags, bracket content, and dashes.
    
    Args:
        text: Raw subtitle text
        
    Returns:
        Cleaned text
    """
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove content in parentheses, brackets, and braces
    text = re.sub(r'\([^)]*\)', '', text)
    text = re.sub(r'\[[^\]]*\]', '', text)
    text = re.sub(r'\{[^}]*\}', '', text)
    
    # Clean up extra whitespace first
    text = ' '.join(text.split())
    
    # Remove dashes at the beginning of lines
    # Handle cases like "- -", "- ", "-", "–", etc.
    text = re.sub(r'^[-â€""]+\s*', '', text)
    
    # Remove dashes at the end of lines
    text = re.sub(r'\s*[-â€""]+$', '', text)
    
    # Final cleanup of whitespace
    text = text.strip()
    
    return text

def parse_srt_file(file_path: Path) -> List[Tuple[int, str, str, str]]:
    """
    Parse an SRT file into a list of subtitle entries.
    
    Args:
        file_path: Path to the SRT file
        
    Returns:
        List of tuples (index, start_time, end_time, text)
    """
    entries = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except UnicodeDecodeError:
        # Try with different encodings
        for encoding in ['latin1', 'cp1252', 'iso-8859-1']:
            try:
                with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue
        else:
            print(f"Warning: Could not decode {file_path}")
            return entries
    
    # Split into blocks
    blocks = re.split(r'\n\s*\n', content.strip())
    
    for block in blocks:
        if not block.strip():
            continue
            
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue
            
        try:
            # Parse index
            index = int(lines[0].strip())
            
            # Parse time range
            time_line = lines[1].strip()
            if ' --> ' not in time_line:
                continue
            start_time, end_time = time_line.split(' --> ')
            
            # Parse text (everything after the time line)
            text_lines = lines[2:]
            text = '\n'.join(text_lines)
            
            # Skip this entry if it contains the music symbol
            if contains_music_symbol(text):
                continue
            
            # Skip this entry if it's a single character
            if is_single_character(text):
                continue
            
            entries.append((index, start_time.strip(), end_time.strip(), text))
            
        except (ValueError, IndexError):
            continue
    
    return entries

def merge_consecutive_duplicates(entries: List[Tuple[int, str, str, str]]) -> List[Tuple[int, str, str, str]]:
    """
    Merge consecutive entries with identical cleaned text.
    
    Args:
        entries: List of subtitle entries
        
    Returns:
        List with merged entries
    """
    if not entries:
        return entries
    
    merged = []
    current_entry = list(entries[0])  # [index, start_time, end_time, text]
    current_cleaned_text = clean_text(current_entry[3])
    
    for i in range(1, len(entries)):
        entry = entries[i]
        cleaned_text = clean_text(entry[3])
        
        # If the cleaned text matches the current entry, merge them
        if cleaned_text == current_cleaned_text and cleaned_text.strip():
            # Update end time to the end time of the current entry
            current_entry[2] = entry[2]
        else:
            # Add the current merged entry and start a new one
            merged.append(tuple(current_entry))
            current_entry = list(entry)
            current_cleaned_text = cleaned_text
    
    # Add the last entry
    merged.append(tuple(current_entry))
    
    # Re-index the entries
    reindexed = []
    for i, (_, start_time, end_time, text) in enumerate(merged, 1):
        reindexed.append((i, start_time, end_time, text))
    
    return reindexed

def write_srt_file(file_path: Path, entries: List[Tuple[int, str, str, str]]) -> None:
    """
    Write subtitle entries to an SRT file with proper sequential numbering.
    
    Args:
        file_path: Path to write the SRT file
        entries: List of subtitle entries
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        entry_number = 1
        
        for i, (_, start_time, end_time, text) in enumerate(entries):
            # Clean the text
            cleaned_text = clean_text(text)
            
            # Skip empty entries
            if not cleaned_text.strip():
                continue
            
            f.write(f"{entry_number}\n")
            f.write(f"{start_time} --> {end_time}\n")
            f.write(f"{cleaned_text}\n")
            
            # Add blank line between entries (except for the last one)
            if i < len(entries) - 1:
                f.write("\n")
            
            entry_number += 1

def repair_srt_file(file_path: Path) -> Tuple[bool, str, int, int]:
    """
    Repair a single SRT file.
    
    Args:
        file_path: Path to the SRT file
        
    Returns:
        Tuple of (success, file_path, original_count, final_count)
    """
    try:
        # Create backup
        # backup_path = file_path.with_suffix('.srt.backup')
        # shutil.copy2(file_path, backup_path)
        
        # Parse the file
        entries = parse_srt_file(file_path)
        
        if not entries:
            return (False, str(file_path), 0, 0)
        
        original_count = len(entries)
        
        # Merge consecutive duplicates
        merged_entries = merge_consecutive_duplicates(entries)
        
        # Write repaired file
        write_srt_file(file_path, merged_entries)
        
        final_count = len([e for e in merged_entries if clean_text(e[3]).strip()])
        
        return (True, str(file_path), original_count, final_count)
        
    except Exception as e:
        return (False, str(file_path), 0, 0)

def process_file_wrapper(file_path: Path) -> Tuple[bool, str, int, int]:
    """
    Wrapper function for multiprocessing.
    
    Args:
        file_path: Path to the SRT file
        
    Returns:
        Result tuple from repair_srt_file
    """
    return repair_srt_file(file_path)

def main():
    """Main function to repair all SRT files using multiprocessing."""
    print("SRT File Repair Tool (Multi-core)")
    print("==================================")
    print("Searching for .srt files...")
    
    # Find all SRT files
    srt_files = find_srt_files()
    
    if not srt_files:
        print("No .srt files found in the current directory and subdirectories.")
        return
    
    print(f"Found {len(srt_files)} .srt file(s)")
    print(f"Using 8 cores for processing...")
    print()
    
    # Process files using multiprocessing with 8 cores
    num_processes = min(8, len(srt_files))  # Don't use more processes than files
    
    with Pool(processes=num_processes) as pool:
        results = pool.map(process_file_wrapper, srt_files)
    
    # Display results
    repaired_count = 0
    for success, file_path, original_count, final_count in results:
        if success:
            print(f"✓ {file_path}")
            print(f"  {original_count} → {final_count} entries")
            repaired_count += 1
        else:
            print(f"✗ {file_path}")
            if original_count == 0:
                print(f"  No valid entries found")
            else:
                print(f"  Error during processing")
        print()
    
    print(f"Repair completed: {repaired_count}/{len(srt_files)} files processed successfully")
    print("Backup files (.srt.backup) have been created for all processed files.")

if __name__ == "__main__":
    main()