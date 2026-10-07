def pytest_configure(config):
    config.addinivalue_line("markers", "live: hits the real Riot / lolworlds APIs (skipped when offline)")
