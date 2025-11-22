#!/usr/bin/env python3
"""
SRT File Repair Script with Pair Synchronization (Multi-core version)

This script finds all .srt files in the current directory and subdirectories,
then repairs them by:
1. Removing HTML tags
2. Removing content in parentheses (), brackets [], and braces {}
3. Skipping entire subtitle blocks containing ♪ symbols (music notation)
4. Skipping subtitle blocks with only a single character
5. Removing leading and trailing dashes (- and –)
6. Merging consecutive subtitle entries with identical text
7. Recreating sequential numbering starting from 1
8. **NEW**: Synchronizing subtitle pairs (_en.srt and _ru.srt):
   - If one interval in EN file contains multiple intervals in RU file, they are merged
   - If one interval in RU file contains multiple intervals in EN file, they are merged
   - This ensures both files have matching time intervals for proper alignment

Usage: python clean_sub_v4.py
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

def find_subtitle_pairs(directory: str = ".") -> List[Tuple[Path, Path]]:
    """
    Find pairs of subtitle files (_en.srt and _ru.srt).

    Args:
        directory: Directory to search in

    Returns:
        List of tuples (en_file, ru_file)
    """
    srt_files = find_srt_files(directory)
    pairs = []

    # Group files by their base name (without _en or _ru suffix)
    en_files = {}
    ru_files = {}

    for file_path in srt_files:
        file_name = file_path.stem  # filename without extension

        if file_name.endswith('_en'):
            base_name = file_name[:-3]  # remove _en
            en_files[base_name] = file_path
        elif file_name.endswith('_ru'):
            base_name = file_name[:-3]  # remove _ru
            ru_files[base_name] = file_path

    # Match pairs
    for base_name, en_file in en_files.items():
        if base_name in ru_files:
            pairs.append((en_file, ru_files[base_name]))

    return pairs

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

def parse_time_to_ms(time_str: str) -> int:
    """
    Parse SRT time format to milliseconds.

    Args:
        time_str: Time string in format "HH:MM:SS,mmm"

    Returns:
        Time in milliseconds
    """
    # Handle both comma and period as millisecond separator
    time_str = time_str.replace(',', '.')
    parts = time_str.split(':')
    if len(parts) != 3:
        return 0

    hours = int(parts[0])
    minutes = int(parts[1])
    seconds_parts = parts[2].split('.')
    seconds = int(seconds_parts[0])
    milliseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0

    return hours * 3600000 + minutes * 60000 + seconds * 1000 + milliseconds

def ms_to_time_str(ms: int) -> str:
    """
    Convert milliseconds to SRT time format.

    Args:
        ms: Time in milliseconds

    Returns:
        Time string in format "HH:MM:SS,mmm"
    """
    hours = ms // 3600000
    ms %= 3600000
    minutes = ms // 60000
    ms %= 60000
    seconds = ms // 1000
    milliseconds = ms % 1000

    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

def intervals_overlap(start1_ms: int, end1_ms: int, start2_ms: int, end2_ms: int) -> bool:
    """
    Check if two time intervals overlap.

    Args:
        start1_ms, end1_ms: First interval in milliseconds
        start2_ms, end2_ms: Second interval in milliseconds

    Returns:
        True if intervals overlap, False otherwise
    """
    return not (end1_ms <= start2_ms or end2_ms <= start1_ms)

def interval_contains(outer_start_ms: int, outer_end_ms: int, inner_start_ms: int, inner_end_ms: int) -> bool:
    """
    Check if outer interval fully contains inner interval.

    Args:
        outer_start_ms, outer_end_ms: Outer interval in milliseconds
        inner_start_ms, inner_end_ms: Inner interval in milliseconds

    Returns:
        True if outer contains inner, False otherwise
    """
    return outer_start_ms <= inner_start_ms and inner_end_ms <= outer_end_ms

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

def synchronize_subtitle_pairs(entries_a: List[Tuple[int, str, str, str]],
                               entries_b: List[Tuple[int, str, str, str]]) -> Tuple[List[Tuple[int, str, str, str]], List[Tuple[int, str, str, str]]]:
    """
    Synchronize two subtitle lists by merging entries that fall within the same time interval.

    If one interval in list A contains multiple intervals from list B, those intervals in B are merged.
    The process continues iteratively until no more merges are needed.

    Args:
        entries_a: First list of subtitle entries (e.g., English)
        entries_b: Second list of subtitle entries (e.g., Russian)

    Returns:
        Tuple of synchronized (entries_a, entries_b)
    """
    if not entries_a or not entries_b:
        return entries_a, entries_b

    max_iterations = 10
    iteration = 0

    while iteration < max_iterations:
        changed = False
        iteration += 1

        # Process list B: merge entries that are contained within a single entry in A
        new_b = []
        b_index = 0

        while b_index < len(entries_b):
            # Find entries in A that might contain multiple B entries
            current_b = entries_b[b_index]
            b_start_ms = parse_time_to_ms(current_b[1])
            b_end_ms = parse_time_to_ms(current_b[2])

            # Find the A entry that overlaps with current B entry
            containing_a = None
            for a_entry in entries_a:
                a_start_ms = parse_time_to_ms(a_entry[1])
                a_end_ms = parse_time_to_ms(a_entry[2])

                if interval_contains(a_start_ms, a_end_ms, b_start_ms, b_end_ms):
                    containing_a = a_entry
                    break

            if containing_a:
                a_start_ms = parse_time_to_ms(containing_a[1])
                a_end_ms = parse_time_to_ms(containing_a[2])

                # Collect all B entries that are contained in this A entry
                entries_to_merge = [current_b]
                next_index = b_index + 1

                while next_index < len(entries_b):
                    next_b = entries_b[next_index]
                    next_b_start_ms = parse_time_to_ms(next_b[1])
                    next_b_end_ms = parse_time_to_ms(next_b[2])

                    if interval_contains(a_start_ms, a_end_ms, next_b_start_ms, next_b_end_ms):
                        entries_to_merge.append(next_b)
                        next_index += 1
                    else:
                        break

                # If we found multiple B entries within one A entry, merge them
                if len(entries_to_merge) > 1:
                    changed = True
                    # Merge texts with space separator
                    merged_text = ' '.join(clean_text(entry[3]) for entry in entries_to_merge)
                    # Use the time range of the containing A entry
                    merged_entry = (0, containing_a[1], containing_a[2], merged_text)
                    new_b.append(merged_entry)
                    b_index = next_index
                else:
                    new_b.append(current_b)
                    b_index += 1
            else:
                new_b.append(current_b)
                b_index += 1

        entries_b = new_b

        # Process list A: merge entries that are contained within a single entry in B
        new_a = []
        a_index = 0

        while a_index < len(entries_a):
            current_a = entries_a[a_index]
            a_start_ms = parse_time_to_ms(current_a[1])
            a_end_ms = parse_time_to_ms(current_a[2])

            # Find the B entry that overlaps with current A entry
            containing_b = None
            for b_entry in entries_b:
                b_start_ms = parse_time_to_ms(b_entry[1])
                b_end_ms = parse_time_to_ms(b_entry[2])

                if interval_contains(b_start_ms, b_end_ms, a_start_ms, a_end_ms):
                    containing_b = b_entry
                    break

            if containing_b:
                b_start_ms = parse_time_to_ms(containing_b[1])
                b_end_ms = parse_time_to_ms(containing_b[2])

                # Collect all A entries that are contained in this B entry
                entries_to_merge = [current_a]
                next_index = a_index + 1

                while next_index < len(entries_a):
                    next_a = entries_a[next_index]
                    next_a_start_ms = parse_time_to_ms(next_a[1])
                    next_a_end_ms = parse_time_to_ms(next_a[2])

                    if interval_contains(b_start_ms, b_end_ms, next_a_start_ms, next_a_end_ms):
                        entries_to_merge.append(next_a)
                        next_index += 1
                    else:
                        break

                # If we found multiple A entries within one B entry, merge them
                if len(entries_to_merge) > 1:
                    changed = True
                    # Merge texts with space separator
                    merged_text = ' '.join(clean_text(entry[3]) for entry in entries_to_merge)
                    # Use the time range of the containing B entry
                    merged_entry = (0, containing_b[1], containing_b[2], merged_text)
                    new_a.append(merged_entry)
                    a_index = next_index
                else:
                    new_a.append(current_a)
                    a_index += 1
            else:
                new_a.append(current_a)
                a_index += 1

        entries_a = new_a

        # If no changes were made, we're done
        if not changed:
            break

    # Re-index both lists
    reindexed_a = []
    for i, (_, start_time, end_time, text) in enumerate(entries_a, 1):
        reindexed_a.append((i, start_time, end_time, text))

    reindexed_b = []
    for i, (_, start_time, end_time, text) in enumerate(entries_b, 1):
        reindexed_b.append((i, start_time, end_time, text))

    return reindexed_a, reindexed_b

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

def process_subtitle_pair(en_file: Path, ru_file: Path) -> Tuple[bool, str, int, int, int, int]:
    """
    Process a pair of subtitle files (English and Russian) with synchronization.

    Args:
        en_file: Path to English subtitle file
        ru_file: Path to Russian subtitle file

    Returns:
        Tuple of (success, pair_name, en_original, en_final, ru_original, ru_final)
    """
    try:
        # Parse both files
        en_entries = parse_srt_file(en_file)
        ru_entries = parse_srt_file(ru_file)

        if not en_entries or not ru_entries:
            return (False, f"{en_file.stem}/{ru_file.stem}", 0, 0, 0, 0)

        en_original = len(en_entries)
        ru_original = len(ru_entries)

        # Merge consecutive duplicates in each file
        en_entries = merge_consecutive_duplicates(en_entries)
        ru_entries = merge_consecutive_duplicates(ru_entries)

        # Synchronize the two subtitle lists
        en_entries, ru_entries = synchronize_subtitle_pairs(en_entries, ru_entries)

        # Write repaired files
        write_srt_file(en_file, en_entries)
        write_srt_file(ru_file, ru_entries)

        en_final = len([e for e in en_entries if clean_text(e[3]).strip()])
        ru_final = len([e for e in ru_entries if clean_text(e[3]).strip()])

        return (True, f"{en_file.stem}/{ru_file.stem}", en_original, en_final, ru_original, ru_final)

    except Exception as e:
        return (False, f"{en_file.stem}/{ru_file.stem}", 0, 0, 0, 0)

def process_pair_wrapper(file_pair: Tuple[Path, Path]) -> Tuple[bool, str, int, int, int, int]:
    """
    Wrapper function for multiprocessing subtitle pairs.

    Args:
        file_pair: Tuple of (en_file, ru_file)

    Returns:
        Result tuple from process_subtitle_pair
    """
    en_file, ru_file = file_pair
    return process_subtitle_pair(en_file, ru_file)

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
    """Main function to repair all SRT files using multiprocessing with pair synchronization."""
    print("SRT File Repair Tool with Pair Synchronization (Multi-core)")
    print("=============================================================")
    print("Searching for .srt file pairs...")

    # Find subtitle pairs (_en.srt and _ru.srt)
    subtitle_pairs = find_subtitle_pairs()

    if not subtitle_pairs:
        print("No subtitle pairs (_en.srt and _ru.srt) found.")
        print()
    else:
        print(f"Found {len(subtitle_pairs)} subtitle pair(s)")
        print(f"Using 8 cores for processing...")
        print()

        # Process pairs using multiprocessing with 8 cores
        num_processes = min(8, len(subtitle_pairs))

        with Pool(processes=num_processes) as pool:
            pair_results = pool.map(process_pair_wrapper, subtitle_pairs)

        # Display pair results
        pair_success_count = 0
        for success, pair_name, en_orig, en_final, ru_orig, ru_final in pair_results:
            if success:
                print(f"✓ {pair_name}")
                print(f"  EN: {en_orig} → {en_final} entries")
                print(f"  RU: {ru_orig} → {ru_final} entries")
                pair_success_count += 1
            else:
                print(f"✗ {pair_name}")
                if en_orig == 0 and ru_orig == 0:
                    print(f"  No valid entries found")
                else:
                    print(f"  Error during processing")
            print()

        print(f"Pair processing completed: {pair_success_count}/{len(subtitle_pairs)} pairs processed successfully")
        print()

    # Find and process single files (files not in pairs)
    all_srt_files = set(find_srt_files())
    paired_files = set()
    for en_file, ru_file in subtitle_pairs:
        paired_files.add(en_file)
        paired_files.add(ru_file)

    single_files = list(all_srt_files - paired_files)

    if not single_files:
        print("No single .srt files found (all files are in pairs).")
    else:
        print(f"Found {len(single_files)} single .srt file(s)")
        print(f"Processing single files...")
        print()

        # Process single files using multiprocessing
        num_processes = min(8, len(single_files))

        with Pool(processes=num_processes) as pool:
            single_results = pool.map(process_file_wrapper, single_files)

        # Display single file results
        single_success_count = 0
        for success, file_path, original_count, final_count in single_results:
            if success:
                print(f"✓ {file_path}")
                print(f"  {original_count} → {final_count} entries")
                single_success_count += 1
            else:
                print(f"✗ {file_path}")
                if original_count == 0:
                    print(f"  No valid entries found")
                else:
                    print(f"  Error during processing")
            print()

        print(f"Single file processing completed: {single_success_count}/{len(single_files)} files processed successfully")
        print()

    print("All processing completed!")
    print("Note: Backup files (.srt.backup) creation is currently disabled.")

if __name__ == "__main__":
    main()