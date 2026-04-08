class Config:
    def __init__(self):
        # default timeout (can be overridden in tests via PropertyMock)
        self._timeout = 10

    @property
    def timeout(self):
        return self._timeout


def fetch_data(api):
    """Call the API client's get method for '/data' and return the result."""
    return api.get("/data")


def save_result(filename, data):
    """Save data to a file (used by tests with mock_open)."""
    with open(filename, "w") as f:
        f.write(data)
