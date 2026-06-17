"""
Security utilities and middleware
"""
import hashlib
import secrets
import bleach
from typing import Optional
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Try to import magic, but make it optional for Windows compatibility
try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False


class SecurityUtils:
    """Security utility functions"""
    
    @staticmethod
    def sanitize_text(text: str) -> str:
        """Sanitize text input to prevent XSS and injection attacks"""
        if not text:
            return ""
        
        # Remove HTML tags and dangerous characters
        clean_text = bleach.clean(text, tags=[], strip=True)
        
        # Remove control characters except newlines and tabs
        clean_text = ''.join(
            char for char in clean_text 
            if ord(char) >= 32 or char in '\n\t'
        )
        
        return clean_text.strip()
    
    @staticmethod
    def generate_secure_filename(original_filename: str) -> str:
        """Generate a secure filename with random component"""
        import os
        name, ext = os.path.splitext(original_filename)
        secure_name = f"{secrets.token_hex(16)}{ext}"
        return secure_name
    
    @staticmethod
    def hash_text(text: str) -> str:
        """Generate hash for text (for caching)"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    @staticmethod
    def validate_audio_file_content(content: bytes, filename: str) -> bool:
        """Validate audio file content - very lenient for development"""
        import os
        
        # Basic checks
        if not content or len(content) < 10:
            return False
        
        # Check file extension
        ext = os.path.splitext(filename)[1].lower()
        allowed_extensions = {'.wav', '.mp3', '.m4a', '.ogg', '.webm', '.flac'}
        
        if ext not in allowed_extensions:
            return False
        
        # For development mode, be very lenient - just check basic size
        # In production, you'd want stricter validation
        if len(content) < 100:
            return False
        
        # Very basic format checks - allow most files through
        try:
            if ext == '.wav':
                # WAV files - very lenient check
                return (content.startswith(b'RIFF') or 
                       b'WAVE' in content[:200] or 
                       b'fmt ' in content[:500] or
                       len(content) > 1000)
            elif ext == '.mp3':
                # MP3 files - very lenient
                return (content.startswith(b'ID3') or 
                       content[0:1] == b'\xff' or  # MP3 frame sync
                       len(content) > 1000)
            elif ext in {'.m4a', '.mp4'}:
                # M4A/MP4 files - lenient check
                return (b'ftyp' in content[:500] or 
                       len(content) > 1000)
            elif ext == '.ogg':
                # OGG files - lenient
                return (content.startswith(b'OggS') or 
                       len(content) > 1000)
            elif ext == '.webm':
                # WebM files - very lenient for browser recordings
                return len(content) > 1000  # Just check size for WebM
            elif ext == '.flac':
                # FLAC files - lenient
                return (content.startswith(b'fLaC') or 
                       len(content) > 1000)
            
            # Default: allow if reasonable size
            return len(content) > 1000
            
        except Exception:
            # If validation fails, allow files with reasonable size
            return len(content) > 1000
    
    @staticmethod
    def validate_file_size(content: bytes, max_size: int) -> bool:
        """Validate file size"""
        return len(content) <= max_size


class RateLimitMiddleware:
    """Simple in-memory rate limiting middleware"""
    
    def __init__(self):
        self.requests = {}  # In production, use Redis
    
    def is_rate_limited(self, client_ip: str, limit: int, window: int) -> bool:
        """Check if client is rate limited"""
        import time
        
        current_time = time.time()
        client_requests = self.requests.get(client_ip, [])
        
        # Remove old requests outside the window
        client_requests = [req_time for req_time in client_requests 
                          if current_time - req_time < window]
        
        if len(client_requests) >= limit:
            return True
        
        # Add current request
        client_requests.append(current_time)
        self.requests[client_ip] = client_requests
        
        return False


# Global rate limiter instance
rate_limiter = RateLimitMiddleware()


def get_client_ip(request: Request) -> str:
    """Extract client IP from request"""
    # Check for forwarded headers (when behind proxy)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    return request.client.host if request.client else "unknown"


def check_rate_limit(request: Request, limit: int = 60, window: int = 60):
    """Check rate limit for request"""
    client_ip = get_client_ip(request)
    
    if rate_limiter.is_rate_limited(client_ip, limit, window):
        raise HTTPException(
            status_code=429,
            detail={
                "error": "rate_limit_exceeded",
                "message": f"Rate limit exceeded: {limit} requests per {window} seconds",
                "retry_after": window
            }
        )