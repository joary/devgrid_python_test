import backend

if __name__ == '__main__':
	S = backend.storage('database.db')
	S.setup_db()
