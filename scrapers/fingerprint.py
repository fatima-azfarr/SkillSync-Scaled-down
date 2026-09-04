"""
SkillSync - SHA-256 Fingerprinting Utility

Creates a unique fingerprint for each listing to prevent duplicates.
Uses SHA-256 (more secure than MD5) to hash a normalized combination of
the listing's title, source, and URL.

How it works:
1. Take the title, source, and URL of a listing
2. Normalize them (lowercase, strip whitespace)
3. Combine them into one string
4. Hash with SHA-256 to get a unique fingerprint
5. If two listings produce the same fingerprint, they're duplicates
"""

import hashlib


def generate_fingerprint(title: str, source: str, source_url: str) -> str:
    """
    Generate a SHA-256 fingerprint for a listing.
    
    The fingerprint is used as a unique key in MongoDB to prevent
    storing the same listing twice across multiple scrape cycles.
    
    Args:
        title: The listing title
        source: The source platform (e.g., 'rozee', 'devpost')
        source_url: The original URL of the listing
        
    Returns:
        A 64-character hexadecimal SHA-256 hash string
        
    Example:
        >>> generate_fingerprint("Python Intern", "rozee", "https://rozee.pk/job/123")
        'a3f2b8c1...'  # 64 chars
    """
    # Step 1: Normalize inputs (lowercase + strip whitespace)
    # This ensures "Python Intern" and "python intern" produce the same hash
    normalized_title = title.lower().strip()
    normalized_source = source.lower().strip()
    normalized_url = source_url.lower().strip()
    
    # Step 2: Combine into a single string with separators
    # The '||' separator prevents accidental collisions between fields
    combined = f"{normalized_title}||{normalized_source}||{normalized_url}"
    
    # Step 3: Create SHA-256 hash
    # encode('utf-8') converts the string to bytes (required by hashlib)
    # hexdigest() returns the hash as a readable hex string
    fingerprint = hashlib.sha256(combined.encode('utf-8')).hexdigest()
    
    return fingerprint
