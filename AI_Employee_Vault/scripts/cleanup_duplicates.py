"""
Cleanup Duplicates Script

Removes duplicate files from Done folder that were created due to the bug.
Keeps the original file (without _N suffix) and removes duplicates.
"""

import re
from pathlib import Path
from collections import defaultdict


def get_base_name(filename: str) -> str:
    """Extract base name without duplicate counter."""
    # Match pattern like FILE_good-money.txt_1.md -> FILE_good-money.txt.md
    match = re.match(r'(.+)_\d+\.md$', filename)
    if match:
        return match.group(1) + '.md'
    return filename


def cleanup_duplicates(done_folder: Path) -> int:
    """Remove duplicate files, keeping the original."""
    removed_count = 0
    
    # Group files by base name
    files_by_base = defaultdict(list)
    
    for file_path in done_folder.glob('*.md'):
        base_name = get_base_name(file_path.name)
        files_by_base[base_name].append(file_path)
    
    # For each group with duplicates, keep original, remove _N versions
    for base_name, files in files_by_base.items():
        if len(files) > 1:
            # Sort: original first (no _N), then duplicates
            files.sort(key=lambda x: '_'+x.name if '_'+base_name.replace('.md','') in x.name else x.name)
            
            # Keep the first one (original), remove rest
            original = files[0]
            duplicates = files[1:]
            
            print(f"Keeping: {original.name}")
            for dup in duplicates:
                print(f"  Removing duplicate: {dup.name}")
                dup.unlink()
                removed_count += 1
    
    return removed_count


def main():
    vault_path = Path(__file__).parent.parent
    done_folder = vault_path / 'Done'
    
    if not done_folder.exists():
        print(f"Done folder not found: {done_folder}")
        return
    
    print(f"Cleaning up duplicates in {done_folder}")
    removed = cleanup_duplicates(done_folder)
    print(f"\nRemoved {removed} duplicate file(s)")
    
    # Show remaining files
    remaining = list(done_folder.glob('*.md'))
    print(f"\nRemaining files in Done: {len(remaining)}")
    for f in sorted(remaining):
        print(f"  - {f.name}")


if __name__ == '__main__':
    main()
