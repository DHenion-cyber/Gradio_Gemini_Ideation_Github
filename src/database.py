class MockConnection:
    def cursor(self):
        return "mock_cursor"
    def close(self):
        pass

def get_connection():
    return MockConnection()