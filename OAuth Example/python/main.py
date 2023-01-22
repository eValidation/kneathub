import webbrowser
import json

import requests
from flask import request, Flask

from variables import token_service_url, client_id, callback_uri, gx_base_url

# The authorization URL to open in a web browser
authorization_url = f'{token_service_url}/Grant/Authorize?client_id={client_id}&response_type=code&redirect_uri={callback_uri}'

# The token endpoint
receive_token_endpoint = f'{token_service_url}/oauth/token'

# The refresh token endpoint
refresh_token_endpoint = f'{token_service_url}/oauth/refresh'


# Open the authorization URL in a web browser
def open_oauth_page():
    webbrowser.open_new(authorization_url)


app = Flask(__name__)


# Process the authorization code
@app.route('/callback_oauth')
def callback_oauth():
    code = request.args.get('code')
    print(code)
    # Create a request to get the access token
    token_response = requests.post(
        f'{receive_token_endpoint}',
        data=f'grant_type=authorization_code&client_id={client_id}&code={code}&redirect_uri={callback_uri}',
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        verify=False)
    if token_response.status_code == 200:
        token = json.loads(token_response.content)
        jwt_token = token['access_token']
        print('Token:')
        print(jwt_token)
        get_users(jwt_token)
        return "<p>Auth code received, back to your console application.</p>"
    else:
        raise Exception('Error getting access token:' + token_response.text)


# Refresh the token
def refresh_token(refresh_token_code):
    # Build the token request
    token_request = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token_code,
        'client_id': client_id,
    }

    # Request the token
    token_response = requests.post(receive_token_endpoint, data=token_request)

    # Return the token
    return token_response.json()


# Create an HTTP Get request to return a list of users, and print on the console the username of the users
def get_users(access_token):
    headers = {'Authorization': 'Bearer ' + access_token}
    response = requests.get(f'{gx_base_url}gx-api/alpha/users', headers=headers, verify=False)
    if response.status_code == 200:
        users_content = response.json()
        user_list = users_content['data']
        username_list = [user_entity['userName'] for user_entity in user_list]
        print(username_list)
    elif response.status_code == 401:
        print('Token expired, refreshing token...')
        refresh_token_response = refresh_token(access_token)
        if refresh_token_response.status_code == 200:
            print('Token refreshed, retrying...')
            get_users(refresh_token_response['access_token'])
        else:
            raise Exception('Error refreshing token:' + refresh_token_response.text)
    else:
        raise Exception('Error getting users:' + response.text)


# Main entry point
if __name__ == '__main__':
    open_oauth_page()

    app.run(port=5198, debug=True)