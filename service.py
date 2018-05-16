from flask import Flask, request
import backend, json
app = Flask(__name__)

S = backend.storage('database.db')

@app.route("/")
def hello():
	return 404

@app.route("/api/")
def default_api():
		return 404

@app.route("/api/add_sensor_record/", methods=["POST"])
def add_sensor_record():
		data = json.loads(request.data);
		if 'record' in data.keys():
			data_dict = backend.validate_sensor_data(data['record']);
			S.record_sensor_info(data_dict);
			#S.get_sensor_data('PowerActive');
			#TODO: n_recs = S.get_n_records()
			#if (n_recs % 1000 == 0 and n_recs != 0):
				#TODO: S.calculate_cluster():
		else:
			return 'Malformed Packet: Request json must have a record field'

		return 'OK'
