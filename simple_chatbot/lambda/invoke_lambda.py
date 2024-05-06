import random
import boto3
import json

def handler(event, context):
    
    
    intent = event.get("interpretations", None)[0]["intent"].get("name", None)
    message = None

    if intent == 'WelcomeIntent':
        message = "Hello! How can I help you?"
    elif intent == 'RequestTowelsIntent':
        message = "Sure! We will send over some towels."
    elif intent == 'ReservationIntent':
        if reserve_cabana_request_handler():
            message = "Sure! Poolside cabana is successfully booked for you. Enjoy!"
        else:
            message = "Sorry, all the pool side cabana are currently booked. Please check back later."
    elif intent == 'AmenitiesIntent':
        message = query_amenity_details(event["inputTranscript"])
        
    else:
        message = "Not sure I understand your request. Please try again."

    response = {
            "sessionState": {
                "dialogAction": {
                    "type": "Close"
                },
                "intent": {
                    'name':intent,
                    'state':'Fulfilled'
                    
                }
            },
            "messages": [
                {
                    "contentType": "PlainText",
                    "content": message
                }
            ]

        }
    return response

def reserve_cabana_request_handler():
    return random.choice([False, True])

def query_amenity_details(user_input):
    
    # Initialize the Bedrock client
    bedrock = boto3.client('bedrock', region_name='us-east-1')
    # Initialize the Bedrock Runtime client
    bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
    foundation_models = bedrock.list_foundation_models()
    matching_model = next((model for model in foundation_models["modelSummaries"]
                    if model.get("modelName") == "Jurassic-2 Ultra"), None)
    
    # Extract the prompt from the event body
    prompt = f"""Answer question using the following context:

        Context:
        Fitness center: Details regarding hours of operation and accessibility are not specified on the website.
        Lounge: Lounge access is included with the stay.
        Free WiFi: Free high-speed WiFi is available throughout the hotel.
        Digital Key: Allows guests to use their smartphone or digital device as a room key.
        Business center: There is a business center present in the building. They are first come first serve.
        Meeting rooms: There are several meeting rooms present in the building. They are first come first serve.
        On-site restaurant: Hours of operation and menus are not specified on the website.
        pool: The hotel has an outdoor swimming pool open year-round.
        Accessible features: There are accessible features offered by the hotel.
        Parking: Self-parking costs $25 per day.
        Breakfast: Full breakfast is available for a fee.
        Pets: A non-refundable fee of $150 applies, with a weight limit of 75 lbs and a size limit of large.
        Package holding: Costs $10 per box per day due to limited storage space.
        {user_input}
        """
    
    # Define the payload for the Bedrock model
    body = json.dumps({
        "prompt": prompt,
        "maxTokens": 2000,
        "temperature": 0.7,
        "topP": 1,
    })
    
    # Invoke the model and get the response
    response = bedrock_runtime.invoke_model(
        body=body,
        modelId=matching_model["modelId"],
        accept='application/json',
        contentType='application/json'
    )
    
    # Parse the response from the model
    response_body = json.loads(response.get('body').read())
    # Extract the answer from the model's response
    answer = response_body.get('completions')[0].get('data').get('text')
    return answer
