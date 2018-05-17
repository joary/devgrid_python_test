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
	''' Get statistics from latest 1000 records 
	
	Ex: curl -X GET http://127.0.0.1:8000/api/statistics/

	Return: '''
	n_clusters = 5;
	n_events = {}
	for i in range(-1, n_clusters+1):
		events = S.get_n_events_in_cluster(i);
		power = S.get_cluster_active_power_average(i);
		n_events.update({str(i): {'nEvents':events, 'powerAverage':power}})
	return json.dumps(n_events)

@app.route("/api/add_sensor_record/", methods=["POST"])
def add_sensor_record():
	''' Insert a new record into database 

	Ex: curl -X POST -H "Content-Type: application/json" -d '{"record": \
	"Device: ID=1; Fw=1607180 1; Evt=2; Alarms: CoilRevesed=OFF; Power: \
	Active=1753W; Reactive=279var; Appearent=403VA; Line: Current=7.35900021; \
	Voltage=230.08V; Phase=-43,841rad; Peaks: 7.33199978;7.311999799999999;\
	7.53000021;7.48400021;7.54300022;7.62900019;7.36499977;7.28599977;\
	7.37200022;7.31899977; FFT Re: 9748;46;303;33;52;19;19;39;-455; \
	FFT Img: 2712;6;-792;-59;1386;-19;963;33;462; \
	UTC Time: 2016-10-4 16:47:50; hz: 49.87; WiFi Strength: -62; \
	Dummy: 20" }' http://127.0.0.1:8000/api/add_sensor_record/
	
	Return: OK
	'''
	try:
		data = json.loads(request.data.decode('utf-8'));
	except json.decoder.JSONDecodeError:
		return 'Wrong Json request', 400
	except typeError:
		return 'Json string must be utf-8', 400

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
