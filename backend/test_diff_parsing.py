
import re

def parse_diff_ranges(patch):
    """
    Parse PR diff to find valid line ranges for comments.
    Returns a list of (start_line, end_line) tuples
    """
    ranges = []
    # Parse hunks: @@ -original,count +new,count @@
    # We only care about the new line numbers (the one with +)
    # Regex captures start_line and optional count
    hunk_headers = re.finditer(r'@@\s*-[0-9,]+\s*\+(\d+)(?:,(\d+))?\s*@@', patch)
    
    for match in hunk_headers:
        start_line = int(match.group(1))
        # If count is missing, it defaults to 1
        count = int(match.group(2)) if match.group(2) else 1
        
        # The valid range covers these lines
        end_line = start_line + count - 1
        ranges.append((start_line, end_line))
            
    return ranges

# Test Cases
patch1 = "@@ -1,5 +1,5 @@\n context\n-removed\n+added\n context" 
# -1,5 (old) +1,5 (new). Start 1, count 5. Range 1-5.
print(f"Patch 1: {parse_diff_ranges(patch1)}")

patch2 = "@@ -10 +15,2 @@\n-line\n+line1\n+line2"
# -10 (old) +15,2 (new). Start 15, count 2. Range 15-16.
print(f"Patch 2: {parse_diff_ranges(patch2)}")

patch3 = """
@@ -10,3 +10,3 @@
 context
+added
 context
@@ -50,2 +60,5 @@
 context
+new1
+new2
+new3
 context
"""
# Hunk 1: 10,3 -> 10-12
# Hunk 2: 60,5 -> 60-64
print(f"Patch 3: {parse_diff_ranges(patch3)}")
