"""
SkillSync - Fingerprint Unit Tests

Tests for the SHA-256 fingerprinting utility.
These ensure that:
1. Same listing always produces the same hash (deterministic)
2. Different listings produce different hashes (unique)
3. The function handles whitespace/case variations correctly
"""

from scrapers.fingerprint import generate_fingerprint


class TestFingerprint:
    """Unit tests for the generate_fingerprint function."""
    
    def test_same_input_same_hash(self):
        """The same listing should always produce the same fingerprint."""
        fp1 = generate_fingerprint("Python Intern", "rozee", "https://rozee.pk/job/123")
        fp2 = generate_fingerprint("Python Intern", "rozee", "https://rozee.pk/job/123")
        
        assert fp1 == fp2, "Same inputs should produce the same hash"
    
    def test_different_input_different_hash(self):
        """Different listings should produce different fingerprints."""
        fp1 = generate_fingerprint("Python Intern", "rozee", "https://rozee.pk/job/123")
        fp2 = generate_fingerprint("Java Developer", "wuzzuf", "https://wuzzuf.net/job/456")
        
        assert fp1 != fp2, "Different inputs should produce different hashes"
    
    def test_case_insensitive(self):
        """Fingerprint should be the same regardless of case."""
        fp_lower = generate_fingerprint("python intern", "rozee", "https://rozee.pk/job/123")
        fp_upper = generate_fingerprint("Python Intern", "Rozee", "https://Rozee.pk/job/123")
        
        assert fp_lower == fp_upper, "Case should not affect the fingerprint"
    
    def test_whitespace_insensitive(self):
        """Extra whitespace should not change the fingerprint."""
        fp_clean = generate_fingerprint("Python Intern", "rozee", "https://rozee.pk/job/123")
        fp_spaces = generate_fingerprint("  Python Intern  ", "  rozee  ", "  https://rozee.pk/job/123  ")
        
        assert fp_clean == fp_spaces, "Extra whitespace should not affect the fingerprint"
    
    def test_hash_is_64_chars(self):
        """SHA-256 hex digest should always be 64 characters long."""
        fp = generate_fingerprint("Test Title", "test_source", "https://example.com")
        
        assert len(fp) == 64, f"SHA-256 should be 64 chars, got {len(fp)}"
    
    def test_hash_is_hexadecimal(self):
        """The fingerprint should only contain hex characters (0-9, a-f)."""
        fp = generate_fingerprint("Test Title", "test_source", "https://example.com")
        
        assert all(c in "0123456789abcdef" for c in fp), \
            "Fingerprint should only contain hex characters"
    
    def test_different_url_different_hash(self):
        """Same title and source but different URL should produce different hash."""
        fp1 = generate_fingerprint("Python Intern", "rozee", "https://rozee.pk/job/123")
        fp2 = generate_fingerprint("Python Intern", "rozee", "https://rozee.pk/job/456")
        
        assert fp1 != fp2, "Different URLs should produce different hashes"
    
    def test_different_source_different_hash(self):
        """Same title but different source should produce different hash."""
        fp1 = generate_fingerprint("Python Intern", "rozee", "https://example.com/job/123")
        fp2 = generate_fingerprint("Python Intern", "wuzzuf", "https://example.com/job/123")
        
        assert fp1 != fp2, "Different sources should produce different hashes"
