from google_auth_oauthlib.flow import InstalledAppFlow
import pickle

SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
flow = InstalledAppFlow.from_client_secrets_file('client_secrets.json', SCOPES)
credentials = flow.run_local_server(port=8080)

with open('token.pickle', 'wb') as f:
    pickle.dump(credentials, f)
    
print('✅ Token created successfully!')