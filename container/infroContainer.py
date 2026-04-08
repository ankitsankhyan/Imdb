from config import DBConfig

def setup_database():
      try:
            db_config = DBConfig()
            # The 'ping' command is the industry standard for connection checks
            db_config.db.command('ping')
            print("✅ Connection Successful: Database is alive and kicking!")
            return db_config.db
      except Exception as e:  
            print(f"❌ Connection Failed: {e}")
            raise e


db = setup_database()