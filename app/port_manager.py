"""Port management for unique Locust instances"""

class PortManager:
    """Manages port allocation for multiple Locust instances"""
    
    def __init__(self, start_port: int = 8090):
        self._start_port = start_port
        self._used_ports = set()
        self._session_ports = {}
    
    def allocate_port(self, session_id: str) -> int:
        """Allocate a port for the given session ID"""
        if session_id in self._session_ports:
            return self._session_ports[session_id]
        
        port = self._start_port
        while port in self._used_ports:
            port += 1
        
        self._used_ports.add(port)
        self._session_ports[session_id] = port
        return port
    
    def release_port(self, session_id: str) -> None:
        """Release the port for the given session ID"""
        if session_id in self._session_ports:
            port = self._session_ports[session_id]
            self._used_ports.discard(port)
            del self._session_ports[session_id]
