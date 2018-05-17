
# Initial Setup:

Base requirements: Python 3, Pip, Git, Curl

Close this repository:
```
git clone https://github.com/joary/devgrid_python_test
```

Install requirements:
```
pip install -r requirements.txt
```

Run unit test:
```
python ./unit_test.py
```

Setup database:
```
./initdb.sh
```

Run service:
```
./run.sh
```

Generate events with curl
```
bash ./events.sh
```
