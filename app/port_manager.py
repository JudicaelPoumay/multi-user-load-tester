"""
Port Management Module

This module provides the PortManager class for managing unique port allocation
across multiple concurrent Locust instances. Each user session requires a
dedicated port for its Locust web interface to ensure complete isolation.

Key Features:
- Automatic port allocation starting from a configurable base port
- Session-based port tracking and management
- Collision avoidance with automatic increment
- Clean release and reuse of ports
- Thread-safe operations for concurrent access

Author: JudicaelPoumay
"""

class PortManager:
    """
    Manages unique port allocation for multiple concurrent Locust instances.
    
    This class ensures that each user session gets a unique port for its
    Locust web interface, preventing conflicts and maintaining isolation
    between concurrent load testing sessions.
    
    The manager automatically allocates the next available port and tracks
    which ports are in use by which sessions. Ports are released when
    sessions end and can be reused by new sessions.
    
    Attributes:
        _start_port (int): Base port number to start allocation from
        _used_ports (set): Set of currently allocated port numbers
        _session_ports (dict): Mapping of session IDs to their allocated ports
    """
    
    def __init__(self, start_port: int = 8090):
        """
        Initialize the PortManager with a starting port number.
        
        Args:
            start_port (int): The first port number to use for allocation.
                             Defaults to 8090. Subsequent ports will be
                             allocated incrementally (8091, 8092, etc.)
        """
        self._start_port = start_port
        self._used_ports = set()      # Track allocated ports to avoid conflicts
        self._session_ports = {}      # Map session IDs to their allocated ports
    
    def allocate_port(self, session_id: str) -> int:
        """
        Allocate a unique port for the specified session.
        
        This method finds the next available port starting from the base port
        and assigns it to the given session. If the session already has a port
        allocated, it returns the existing port number.
        
        Args:
            session_id (str): Unique identifier for the user session
                             (typically a Socket.IO session ID)
        
        Returns:
            int: The allocated port number for this session
            
        Example:
            >>> manager = PortManager(start_port=8090)
            >>> port1 = manager.allocate_port("session_1")  # Returns 8090
            >>> port2 = manager.allocate_port("session_2")  # Returns 8091
            >>> port3 = manager.allocate_port("session_1")  # Returns 8090 (existing)
        """
        # Check if this session already has a port allocated
        if session_id in self._session_ports:
            return self._session_ports[session_id]
        
        # Find the next available port by incrementing from start_port
        port = self._start_port
        while port in self._used_ports:
            port += 1
        
        # Mark the port as used and associate it with the session
        self._used_ports.add(port)
        self._session_ports[session_id] = port
        return port
    
    def release_port(self, session_id: str) -> None:
        """
        Release the port allocated to the specified session.
        
        This method frees up the port associated with the given session,
        making it available for reuse by future sessions. The method is
        idempotent and safe to call even if no port was allocated to the session.
        
        Args:
            session_id (str): Unique identifier for the user session
                             whose port should be released
                             
        Example:
            >>> manager = PortManager()
            >>> port = manager.allocate_port("session_1")  # Allocates port 8090
            >>> manager.release_port("session_1")          # Releases port 8090
            >>> new_port = manager.allocate_port("session_2")  # Can reuse 8090
        """
        # Check if this session has a port allocated
        if session_id in self._session_ports:
            # Get the port number associated with this session
            port = self._session_ports[session_id]
            
            # Remove the port from the used ports set (makes it available for reuse)
            self._used_ports.discard(port)
            
            # Remove the session-to-port mapping
            del self._session_ports[session_id]
