import requests

def send_case_update(chat_id, case_number, new_status, bot_token="7311331973:AAGhs8sqwLzhjd3DBvudnI2zmNGXNS2Ev3M"):
    # Format the message
    message = f"Case number {case_number} status has been changed to '{new_status}'"
    
    # Telegram Bot API URL
    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    
    # Parameters for the API request
    params = {
        'chat_id': chat_id,
        'text': message
    }
    
    # Send the request
    response = requests.get(url, params=params)
    
    # Check the response status code and print details
    if response.status_code == 200:
        print('Message sent successfully!')
    else:
        print(f'Failed to send message. Error: {response.status_code}, Response: {response.text}')

