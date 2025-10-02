from services.firebase_client import FirebaseClient

client = FirebaseClient()
print("Firebase client created successfully!")
print(f"Database URL: {client.database_url}")