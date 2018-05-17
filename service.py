from flask import Flask, request
import backend, json
app = Flask(__name__)
app.config['DATABASE'] = 'database.db';

S = backend.storage(app)

@app.cli.command()
def initdb():
	"""Initialize the database."""
	S.init_db();
	print('Database Initialized')

@app.route("/api/statistics/", methods=["GET"])
def get_statistics():
	n_clusters = 5;#S.get_n_clusters();
	n_events = {}
	for i in range(n_clusters+1):
		events = S.get_n_events_in_cluster(i);
		power = S.get_cluster_active_power_average(i);
		n_events.update({str(i): {'nEvents':events, 'powerAverage':power}});
	#print(n_events)
	return json.dumps(n_events)

@app.route("/api/add_sensor_record/", methods=["POST"])
def add_sensor_record():
	''' Insert a new record into database '''
	try:
		data = json.loads(request.data);
	except json.decoder.JSONDecodeError:
		return 'Wrong Json request', 400

	if 'record' in data.keys():
		data_dict = backend.validate_sensor_data(data['record']);
		if(data_dict == -2):
			return 'wrong sensor data information', 400

		S.record_sensor_info(data_dict);
		n_recs = S.get_n_records()
		if (n_recs % 1000 == 0 and n_recs != 0):
			S.calculate_cluster()
	else:
		return 'json must have a record field', 400

	return 'OK', 200
