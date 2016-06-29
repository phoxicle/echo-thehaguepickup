"""
This sample demonstrates a simple skill built with the Amazon Alexa Skills Kit.
The Intent Schema, Custom Slots, and Sample Utterances for this skill, as well
as testing instructions are located at http://amzn.to/1LzFrj6

For additional samples, visit the Alexa Skills Kit Getting Started guide at
http://amzn.to/1LGWsLG
"""

from __future__ import print_function
from HTMLParser import HTMLParser
from itertools import izip
from datetime import datetime, timedelta, date
import urllib2

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" + event['session']['application']['applicationId'])

    if (event['session']['application']['applicationId'] != "amzn1.echo-sdk-ams.app.8b6d1a64-da37-4e3f-ac18-be4f7da53e24"):
        raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']}, event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])


def on_session_started(session_started_request, session):
    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they want """
    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """
    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to intent handlers
    if intent_name == "WhenIntent":
        return get_when_response(intent, session)
    elif intent_name == "AMAZON.StopIntent" or intent_name == "AMAZON.CancelIntent":
        return
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session. Is not called when the skill returns should_end_session=true """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here

# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response():
    card_title = "Welcome"
    speech_output = "What is your zip code and house number?"
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "Ask me when your pick up days are by saying, " \
            "zip code two five six two x l, house number three."
    should_end_session = False
    return build_response({}, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def get_when_response(intent, session):
    session_attributes = {}
    card_title = intent['name']

    # Get the zip code, either from user now or from session
    zip_code = None
    if ('ZipNumber' in intent['slots'] and 'value' in intent['slots'] ['ZipNumber']
        and 'ZipFirstLetter' in intent['slots'] and 'value' in intent['slots'] ['ZipFirstLetter']
        and 'ZipSecondLetter' in intent['slots'] and 'value' in intent['slots'] ['ZipSecondLetter']):

        zip_code = intent['slots']['ZipNumber']['value'] + intent['slots']['ZipFirstLetter']['value'] + intent['slots']['ZipSecondLetter']['value'] 
        print("Got new zip code: " + zip_code)
    elif (session.get('attributes', {}) and "zip_code" in session.get('attributes', {})):

        zip_code = session['attributes']['zip_code']
        print("Using session zip code: " + zip_code)

    # Get the house number (always gotten from the user, since we don't store it)
    house_number = None
    if ('HouseNumber' in intent['slots'] and 'value' in intent['slots'] ['HouseNumber']):
        house_number = intent['slots']['HouseNumber']['value']
        print("Got house number: " + house_number)

    if zip_code:
        session_attributes['zip_code'] = zip_code

        if house_number:
            print("Got house number: " + house_number + ". Calculate response")
            # No reason to store house_number in session since we always do zip first. Just give them the response.
            speech_output = calculate_when_response(zip_code, house_number)
            reprompt_text = ""
            should_end_session = True
        else:
            print("Got zip code, but no house number. Prompting.")
            speech_output = "Which house number?"
            reprompt_text = "Ask me when your pick up days are by saying, " \
                        "house number three."
            should_end_session = False
    else:
        speech_output = "Which zip code and house number?"
        reprompt_text = "Ask me when your pick up days are by saying, " \
                    "zip code two five six two x l, house number three."
        should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def calculate_when_response(zip_code, house_number):
    print("Getting when response for zip {} and house number {}".format(zip_code, house_number))
    text = ""

    # Scrape the pick up days from the website
    print("Retrieving HTML...")
    html = HTMLLoader.get_html(zip_code, house_number)
   
    print("Parsing HTML...")
    parser = PickUpHTMLParser()
    try:
        parser.feed(html)
        data_pairwise = parser.get_data_pairwise()
    except:
        print("Error parsing HTML")
        text = "Error fetching HTTP response"

    print("Translating data...")
    pick_up_days = []
    for type_dutch, date_dutch in data_pairwise:
        try:
            translated = PickUpTranslator.translate(type_dutch, date_dutch)
        except:
            translated = "Translation error"
        pick_up_days.append(translated)

    text = "The next pick up days for {} number {} are: {}".format(zip_code, house_number, ", ".join(pick_up_days))
    print("Calculated full text: " + text)
    return text

# --------------- Helpers that build all of the responses ----------------------


def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': 'SessionSpeechlet - ' + title,
            'content': 'SessionSpeechlet - ' + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }

class PickUpHTMLParser(HTMLParser):

    # TODO use instance variables
    in_inzameldata = False
    data = []

    def handle_endtag(self, tag):
        if tag == "ul":
            PickUpHTMLParser.in_inzameldata = False

    def handle_data(self, data):
        if PickUpHTMLParser.in_inzameldata:
            print("Encountered some data  :" + data)
            PickUpHTMLParser.data.append(data)
        if data == "Eerstvolgende inzameldata":
            print("in inzameldata")
            PickUpHTMLParser.in_inzameldata = True

    def get_data_pairwise(self):
        data_iter = iter(PickUpHTMLParser.data)
        data_pairwise = izip(data_iter, data_iter)
        return data_pairwise

class PickUpTranslator:
    days = {
        "maandag" : "monday",
        "dinsdag" : "tuesday",
        "woensdag" : "wednesday",
        "donderdag" : "thursday",
        "vrijdag" : "friday",
        "zaterdag" : "saturday",
        "zondag" : "sunday"
    }
    months = {
        "januari" : "january",
        "februari" : "february",
        "maart" : "march",
        "april" : "april",
        "mei" : "may",
        "juni" : "june",
        "juli" : "july",
        "augustus" : "august",
        "september" : "september",
        "oktober" : "october",
        "november" : "november",
        "december" : "december"
    }
    types = {
        "papier" : "paper"
    }

    @staticmethod
    def translate(type_dutch, date_dutch):
        print("Translating type '{}' and date '{}'".format(type_dutch, date_dutch))
        # Date Ex: Donderdag 30 juni
        # Type Ex: Papier
        type_dutch = type_dutch.lower()
        date_dutch = date_dutch.lower()

        [dayofweek_dutch, numday, month_dutch] = date_dutch.split()

        if type_dutch in PickUpTranslator.types:
            type_english = PickUpTranslator.types[type_dutch]
        else:
            print("Falling back to dutch type")
            type_english = type_dutch
        
        translated = '{} on {}, {} {};'.format(
            type_english, 
            PickUpTranslator.days[dayofweek_dutch.lower()], 
            PickUpTranslator.months[month_dutch.lower()] ,
            numday)
        
        print("Translated to: " + translated)
        return translated

# Retrieve URLs like: http://huisvuilkalender.denhaag.nl/HuisVuilFrontOffice/Resultaat/2562XL/108/+/11-06-2016/11-07-2016
class HTMLLoader:

    @staticmethod
    def get_html(zip_code, house_number):
        from_date = date.today();
        to_date = from_date + timedelta(days=40) # Get sufficiently many to days to get the next pick-up day.

        from_date_str = "{}-{}-{}".format(from_date.day, from_date.month, from_date.year)
        to_date_str = "{}-{}-{}".format(to_date.day, to_date.month, to_date.year)

        url = "http://huisvuilkalender.denhaag.nl/HuisVuilFrontOffice/Resultaat/{}/{}/+/{}/{}".format(zip_code, house_number, from_date, to_date)
        print("Opening URL: " + url)
        html = urllib2.urlopen(url).read()
        return html