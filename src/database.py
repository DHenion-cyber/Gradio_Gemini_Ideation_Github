"""Provides a mock database connection for testing or development purposes."""
class MockConnection:
    def cursor(self):
        return "mock_cursor"
    def close(self):
        pass

def get_connection():
    return MockConnection()