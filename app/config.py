import os

API_TEST_URL = "http://localhost/test"
API_URL = os.environ.get('API_URL', API_TEST_URL)

# Or, specify it manually here:
#API_URL = "https://nextcloud.site/apps/cospend/api/projects/<project>/<password>"
