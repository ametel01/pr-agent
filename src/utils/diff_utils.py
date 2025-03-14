"""
Utility functions for handling diffs and patches.
"""

import logging
import re
from typing import Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


def parse_patch(patch: str) -> List[Dict]:
    """Parse a patch into a list of hunks.
    
    Args:
        patch: The patch string
        
    Returns:
        List of hunks, each containing line information
    """
    if not patch:
        return []
    
    hunks = []
    current_hunk = None
    
    for line in patch.split("\n"):
        # New hunk
        if line.startswith("@@"):
            if current_hunk:
                hunks.append(current_hunk)
            
            # Parse hunk header
            match = re.match(r"@@ -(\d+),(\d+) \+(\d+),(\d+) @@", line)
            if match:
                old_start, old_count, new_start, new_count = map(int, match.groups())
                current_hunk = {
                    "header": line,
                    "old_start": old_start,
                    "old_count": old_count,
                    "new_start": new_start,
                    "new_count": new_count,
                    "lines": []
                }
        elif current_hunk is not None:
            current_hunk["lines"].append(line)
    
    # Add the last hunk
    if current_hunk:
        hunks.append(current_hunk)
    
    return hunks


def map_line_to_position(patch: str, line_number: int, is_new_file: bool = True) -> Optional[int]:
    """Map a line number in the file to a position in the diff.
    
    Args:
        patch: The patch string
        line_number: Line number in the file
        is_new_file: Whether to use the new file line numbers (True) or old file line numbers (False)
        
    Returns:
        Position in the diff, or None if not found
    """
    hunks = parse_patch(patch)
    
    # Track position in the diff
    position = 0
    
    for hunk in hunks:
        # Skip the hunk header
        position += 1
        
        # Get the starting line number for this hunk
        start_line = hunk["new_start"] if is_new_file else hunk["old_start"]
        
        # Track the current line number in the file
        current_line = start_line
        
        # Check each line in the hunk
        for line in hunk["lines"]:
            # Increment position for each line in the hunk
            position += 1
            
            # Skip lines that don't exist in the target file
            if is_new_file and line.startswith("-"):
                continue
            if not is_new_file and line.startswith("+"):
                continue
            
            # Check if this is the line we're looking for
            if current_line == line_number:
                return position
            
            # Increment the current line number
            if not line.startswith("-" if is_new_file else "+"):
                current_line += 1
    
    # Line not found in the diff
    return None


def extract_code_from_diff(diff: str, context_lines: int = 3) -> str:
    """Extract the code from a diff, focusing on the changes.
    
    Args:
        diff: The diff string
        context_lines: Number of context lines to include around changes
        
    Returns:
        Extracted code with changes highlighted
    """
    if not diff:
        return ""
    
    lines = diff.split("\n")
    result = []
    
    # Skip the first few lines if they're diff metadata
    start_idx = 0
    for i, line in enumerate(lines):
        if line.startswith("@@"):
            start_idx = i
            break
    
    # Process the diff
    for line in lines[start_idx:]:
        # Skip diff metadata
        if line.startswith("diff ") or line.startswith("index ") or line.startswith("---") or line.startswith("+++"):
            continue
        
        # Include hunk headers
        if line.startswith("@@"):
            result.append(line)
        else:
            result.append(line)
    
    return "\n".join(result)


def get_file_extension(filename: str) -> str:
    """Get the file extension from a filename.
    
    Args:
        filename: The filename
        
    Returns:
        File extension (without the dot)
    """
    parts = filename.split(".")
    if len(parts) > 1:
        return parts[-1].lower()
    return ""


def is_binary_file(filename: str) -> bool:
    """Check if a file is likely to be binary based on its extension.
    
    Args:
        filename: The filename
        
    Returns:
        True if the file is likely binary, False otherwise
    """
    binary_extensions = {
        # Images
        "png", "jpg", "jpeg", "gif", "bmp", "ico", "svg", "webp",
        # Audio
        "mp3", "wav", "ogg", "flac", "aac",
        # Video
        "mp4", "avi", "mkv", "mov", "webm",
        # Documents
        "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx",
        # Archives
        "zip", "tar", "gz", "rar", "7z",
        # Executables
        "exe", "dll", "so", "dylib",
        # Other
        "bin", "dat"
    }
    
    extension = get_file_extension(filename)
    return extension in binary_extensions 