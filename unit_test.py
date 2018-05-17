import os
import service
import unittest
import tempfile
import sample_data

class FlaskrTestCase(unittest.TestCase):

    def setUp(self):
        self.db_fd, service.app.config['DATABASE'] = tempfile.mkstemp()
        service.app.testing = True
        self.app = service.app.test_client()
        service.S.init_db(service.app.config['DATABASE']);

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(service.app.config['DATABASE'])

    def test_insert_sensor_record(self):
        rv = self.app.post('/api/add_sensor_record/',data=sample_data.events[0])
        assert b'OK' in rv.data

if __name__ == '__main__':
    unittest.main()
