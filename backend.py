import sqlite3, re, os
from numpy import array, fromstring

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
	record_cnt = 0;

	def __init__(self, database):
		# Check if the file exists
		if(os.path.isfile(database)):
			self.conn = sqlite3.connect(database)
			c = self.conn.cursor()
			self.record_cnt = c.execute("SELECT COUNT(*) FROM sensor_data").fetchone()[0]
		else:
			self.conn = sqlite3.connect(database)
	
	def setup_db(self):
		c = self.conn.cursor()
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
			Hz REAL \
			);''')
		self.conn.commit()
		self.conn.close()
		
	def record_sensor_info(self, D):
		c = self.conn.cursor()
		sql_cmd = "INSERT INTO sensor_data VALUES (?,?,?,?,?,?,?,?,?,?)"
		peaks = D['peaks'].tostring()
		fft_c = D['fft'].tostring()
		c.execute(sql_cmd, (D['devid'], D['active_power'], D['reactive_power'], 
			D['appearent_power'], D['current_line'], D['voltage_line'], D['phase_line'],
			peaks, fft_c, D['freq']));
		self.conn.commit()
		
		self.record_cnt += 1;
		
		if(self.record_cnt % 1000 == 0):
			dump_results();

	def get_sensor_data(self, type_s):
		c = self.conn.cursor()
		sql_cmd = "SELECT %s from sensor_data" % (type_s)
		ret = c.execute(sql_cmd);
		if type_s in ['Peaks', 'FFT']:
			data = [fromstring(i[0]) for i in ret]
		else:
			data = [i[0] for i in ret]
		return data;

	def __end__(self):
		self.conn.close()
	
	
