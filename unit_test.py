import os
import service
import unittest
import tempfile
from sample_data import events

class FlaskrTestCase(unittest.TestCase):

    def setUp(self):
        self.db_fd, service.app.config['DATABASE'] = tempfile.mkstemp()
        service.app.testing = True
        self.app = service.app.test_client()
        service.S.init_db();

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(service.app.config['DATABASE'])

    def test_insert_sensor_record(self):
        rv = self.app.post('/api/add_sensor_record/',data=events[0])
        print(rv.data)
        assert rv.status_code == 200

    def test_insert_nojson_sensor_record(self):
        rv = self.app.post('/api/add_sensor_record/',data='{}')
        print(rv.data)
        assert rv.status_code == 400

    def test_insert_wrong_json_sensor_record(self):
        rv = self.app.post('/api/add_sensor_record/',data='{"record": "nothing"}')
        print(rv.data)
        assert rv.status_code == 400

    def test_insert_1k_sensors(self):
        for e in events:
            self.app.post('/api/add_sensor_record/',data=e)
        rv = self.app.get('/api/statistics/')
        print(rv.data)
        assert rv.status_code == 200

if __name__ == '__main__':
    unittest.main()
