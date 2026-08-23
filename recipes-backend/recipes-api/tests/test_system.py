from unittest.mock import patch

from tests.test_base import BaseTestCase


class TestSystemRoutes(BaseTestCase):

    # ============================================================
    # Liveness probe - application is alive
    # ============================================================

    def test_health_probe(self):
        response = self.client.get('/system/health')

        self.assertEqual(response.status_code, 200)

        data = response.get_json()

        self.assertEqual(
            data.get('status'),
            'healthy'
        )

    # ============================================================
    # Readiness probe - database is available
    # ============================================================

    def test_readiness_probe_success(self):
        response = self.client.get('/system/ready')

        self.assertEqual(response.status_code, 200)

        data = response.get_json()

        self.assertEqual(
            data.get('status'),
            'ready'
        )

    # ============================================================
    # Readiness probe - database is unavailable
    # ============================================================

    @patch('views.system_views.db.session.execute')
    def test_readiness_probe_database_failure(self, mock_execute):
        mock_execute.side_effect = Exception(
            'Database unavailable'
        )

        response = self.client.get('/system/ready')

        self.assertEqual(response.status_code, 503)

        data = response.get_json()

        self.assertEqual(
            data.get('status'),
            'not_ready'
        )

    # ============================================================
    # Startup probe - application initialization succeeded
    # ============================================================

    def test_startup_probe_success(self):
        response = self.client.get('/system/startup')

        self.assertEqual(response.status_code, 200)

        data = response.get_json()

        self.assertEqual(
            data.get('status'),
            'started'
        )

    # ============================================================
    # Startup probe - database is unavailable
    # ============================================================

    @patch('views.system_views.db.session.execute')
    def test_startup_probe_database_failure(self, mock_execute):
        mock_execute.side_effect = Exception(
            'Database unavailable'
        )

        response = self.client.get('/system/startup')

        self.assertEqual(response.status_code, 503)

        data = response.get_json()

        self.assertEqual(
            data.get('status'),
            'starting'
        )