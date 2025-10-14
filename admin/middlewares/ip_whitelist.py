"""IP Whitelist Middleware for admin access control."""

import ipaddress
from typing import List, Optional
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from config.settings import settings


class IPWhitelistMiddleware(BaseHTTPMiddleware):
    """Middleware to restrict admin access to whitelisted IP addresses."""

    def __init__(self, app, whitelist: Optional[List[str]] = None):
        super().__init__(app)
        self.whitelist = whitelist or self._get_whitelist_from_settings()
        self.allowed_networks = self._parse_networks(self.whitelist)

    def _get_whitelist_from_settings(self) -> List[str]:
        """Get IP whitelist from settings."""
        allowed_ips = getattr(settings.admin, 'allowed_ips', '')
        if not allowed_ips:
            return []
        
        # Split by comma and clean up
        return [ip.strip() for ip in allowed_ips.split(',') if ip.strip()]

    def _parse_networks(self, ip_list: List[str]) -> List[ipaddress.IPv4Network]:
        """Parse IP addresses and CIDR blocks into network objects."""
        networks = []
        
        for ip_str in ip_list:
            try:
                # Handle CIDR notation (e.g., 192.168.1.0/24)
                if '/' in ip_str:
                    network = ipaddress.IPv4Network(ip_str, strict=False)
                else:
                    # Single IP address (e.g., 192.168.1.1)
                    network = ipaddress.IPv4Network(f"{ip_str}/32", strict=False)
                
                networks.append(network)
            except (ipaddress.AddressValueError, ValueError) as e:
                print(f"Warning: Invalid IP address '{ip_str}': {e}")
                continue
        
        return networks

    def _is_ip_allowed(self, client_ip: str) -> bool:
        """Check if client IP is in the whitelist."""
        if not self.allowed_networks:
            # If no whitelist is configured, allow all IPs
            return True
        
        try:
            client_ip_obj = ipaddress.IPv4Address(client_ip)
            
            # Check if client IP is in any of the allowed networks
            for network in self.allowed_networks:
                if client_ip_obj in network:
                    return True
            
            return False
            
        except ipaddress.AddressValueError:
            # Invalid IP address
            return False

    def _is_admin_route(self, path: str) -> bool:
        """Check if the request is for admin routes."""
        return path.startswith('/admin') or path.startswith('/dashboard')

    async def dispatch(self, request: Request, call_next):
        """Process the request and check IP whitelist."""
        
        # Only apply whitelist to admin routes
        if not self._is_admin_route(request.url.path):
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Check if IP is allowed
        if not self._is_ip_allowed(client_ip):
            # Log the blocked attempt
            print(f"🚫 Blocked admin access attempt from IP: {client_ip}")
            
            # Return 403 Forbidden
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. IP address {client_ip} is not authorized to access admin panel."
            )
        
        # IP is allowed, continue with the request
        response = await call_next(request)
        return response


def create_ip_whitelist_middleware(app, whitelist: Optional[List[str]] = None):
    """Create and configure IP whitelist middleware."""
    return IPWhitelistMiddleware(app, whitelist)


# Example usage and configuration
def get_default_whitelist() -> List[str]:
    """Get default IP whitelist for common scenarios."""
    return [
        "127.0.0.1",      # Localhost
        "::1",            # IPv6 localhost
        "192.168.1.0/24", # Local network
        "10.0.0.0/8",     # Private network
        "172.16.0.0/12",  # Private network
    ]


def is_development_mode() -> bool:
    """Check if running in development mode."""
    return getattr(settings.app, 'debug', False)


def should_enable_whitelist() -> bool:
    """Determine if IP whitelist should be enabled."""
    # Enable whitelist in production, disable in development
    return not is_development_mode()
