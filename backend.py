import sqlite3, re, os
from numpy import array, fromstring, mean
from datetime import datetime
from sklearn.cluster import MeanShift, estimate_bandwidth
# TODO tratar os erros

def validate_sensor_data(data_str):
	# Divide data by type of information
	classes_regex = '(Device|Alarms|Power|Line|Peaks|FFT Re|FFT Img|UTC Time|hz|WiFi Strength|Dummy):';
	classes = re.split(classes_regex, data_str);
	device_info = classes[2].split(';')  # [ID=.., Fw=.., Evt=...]
	alarms_info = classes[4].split(';')  # [CoilRevesed=...]
	power_info  = classes[6].split(';')  # [Active=.. , Reactive=.., Appearent=..]
	line_info   = classes[8].split(';')  # [Current=.. , Voltage=.., Phase=..]
	peaks_info  = classes[10].split(';') # [.., .., ]
	fft_re_info = classes[12].split(';')
	fft_im_info = classes[14].split(';')
	utc_time    = classes[16].split(';')
	hz          = classes[18].split(';')
	
	# Recreate the FFT complex data
	# Avoid the last sample since it is an empty string
	fft_re = array([float(i) for i in fft_re_info[:-1]]); 
	fft_im = array([float(i) for i in fft_im_info[:-1]]);
	fft_c = fft_re + 1j*fft_im;
	
	# Get just the usefull information for this application
	
	ret = {};
	ret.update({'devid'          : int(device_info[0].split('=')[1])})
	ret.update({'active_power'   : float(power_info[0].split('=')[1].replace('W',''))})
	ret.update({'reactive_power' : float(power_info[1].split('=')[1].replace('var',''))})
	ret.update({'appearent_power': float(power_info[2].split('=')[1].replace('VA',''))})
	ret.update({'current_line'   : float(line_info[0].split('=')[1])})
	ret.update({'voltage_line'   : float(line_info[1].split('=')[1].replace('V',''))})
	ret.update({'phase_line'     : float(line_info[2].split('=')[1].replace('rad','').replace(',','.'))})
	ret.update({'peaks'          : array([float(i) for i in peaks_info[:-1]])})
	ret.update({'freq'           : float(hz[0].split(';')[0])})
	ret.update({'fft'            : array(fft_c)})
	return ret;

class storage():
	def __init__(self, app):
		self.record_cnt = 0;
		self.id_db_open = False;
		self.app = app;
	
	def init_db(self):
		''' Function to create and initialize database
		This functino should run only once at the service deployment'''
		self.conn = sqlite3.connect(self.app.config['DATABASE'])
		c = self.conn.cursor()
		c.execute('''DROP TABLE sensor_data''');
		c.execute('''CREATE TABLE sensor_data (\
			devid INTEGER, \
			PowerActive REAL, \
			PowerReactive REAL, \
			PowerAppearent REAL, \
			LineCurrent REAL, \
			LineVoltage REAL, \
			LinePhase REAL, \
			Peaks BLOB, \
			FFT BLOB, \
			Hz REAL, \
			InsertTimestamp TEXT, \
			Label REAL \
			);''')
		self.conn.commit()
		self.conn.close()

	def get_db_cursor(self):
		''' Return a cursor to the configured'''
		if not self.id_db_open:
			self.conn = sqlite3.connect(self.app.config['DATABASE']);
			self.is_db_open = True;
		return self.conn.cursor()

	def record_sensor_info(self, D):
		c = self.get_db_cursor()
		sql_cmd = "INSERT INTO sensor_data ( \
			devid, PowerActive, PowerReactive, PowerAppearent, LineCurrent,\
			LineVoltage, LinePhase, Peaks, FFT, Hz, InsertTimestamp) \
			VALUES (?,?,?,?,?,?,?,?,?,?,?)"

		peaks = D['peaks'].tostring()
		fft_c = D['fft'].tostring()
		ts = datetime.now().isoformat()
		c.execute(sql_cmd, (D['devid'], D['active_power'], D['reactive_power'], 
			D['appearent_power'], D['current_line'], D['voltage_line'], D['phase_line'],
			peaks, fft_c, D['freq'], ts));
		self.conn.commit()
		self.record_cnt += 1;
		
	def get_n_records(self):
		return self.record_cnt;

	def get_sensor_data(self, type_s):
		c = self.get_db_cursor()
		sql_cmd = "SELECT %s from sensor_data ORDER BY InsertTimestamp DESC \
		LIMIT 1000" % (type_s)
		ret = c.execute(sql_cmd).fetchall();
		if type_s in ['Peaks', 'FFT']:
			data = [fromstring(i[0]) for i in ret]
		else:
			data = [i[0] for i in ret]
		return data;
	
	def set_meas_labels(self, ids, labels):
		if(len(ids) != len(labels)):
			print("Id and label vector must have the same length")
			return -1;
		
		sql_cmd = "UPDATE sensor_data SET Label = {} WHERE ROWID = {}";
		c = self.get_db_cursor()
		c.execute("BEGIN TRANSACTION");
		for i in range(len(ids)):
			ret = c.execute(sql_cmd.format(labels[i], ids[i]));
			#print(sql_cmd.format(labels[i], ids[i]))
		c.execute("END TRANSACTION");

	def get_cluster_input_data(self):
		sql_cmd = "SELECT rowid, PowerActive, PowerReactive, PowerAppearent, \
			LineCurrent, LineVoltage, Peaks \
			FROM sensor_data ORDER BY InsertTimestamp DESC LIMIT 1000"
		c = self.get_db_cursor()
		info = c.execute(sql_cmd).fetchall();
		
		ids = [i[0] for i in info];
		# Get usefull data from sql request:
		# Skip the id and group the real vaules, 
		# Convert blob data to list and get just the first 3 transients
		data = [list(i[1:-1]) + list(fromstring(i[-1])[0:3]) for i in info]
		return (ids, data); 

	def calculate_cluster(self):
		(ids, data) = self.get_cluster_input_data();
		
		bandwidth = estimate_bandwidth(data, quantile=0.2, n_samples=200)
		ms = MeanShift(bandwidth=bandwidth, cluster_all=False, bin_seeding=True)
		labels = ms.fit_predict(data)
		
		self.set_meas_labels(ids, list(labels));
		
		return (ids, labels)
		
	def get_n_events_in_cluster(self, cluster):
		c = self.get_db_cursor()
		sql_cmd = "SELECT COUNT(*) FROM sensor_data WHERE Label={}".format(cluster);
		return c.execute(sql_cmd).fetchone()[0]

	def get_cluster_active_power_average(self, cluster):
		c = self.get_db_cursor()
		sql_cmd = "SELECT PowerActive FROM sensor_data WHERE Label={}".format(cluster);
		power = c.execute(sql_cmd).fetchall();
		#print(power)
		return mean(power);

	def __end__(self):
		self.conn.close()
	
	
