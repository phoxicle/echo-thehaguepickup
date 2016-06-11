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
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #     raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])


def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "WhenIntent":
        return get_when_response(intent, session)
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here

# --------------- Functions that control the skill's behavior ------------------


def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """
    card_title = "Welcome"
    speech_output = "Welcome to The Hague Pick Up" \
                    "Ask me when your pick up days are by saying, " \
                    "when in zip code two five six two x l."
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "Ask me when your pick up days are by saying, " \
                    "when for two five six two x l."
    should_end_session = False
    return build_response({}, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Bye and keep recycling!"
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))


def get_when_response(intent, session):
    
    card_title = intent['name']

    if ('ZipNumber' in intent['slots'] and 'value' in intent['slots'] ['ZipNumber']
        and 'ZipFirstLetter' in intent['slots'] and 'value' in intent['slots'] ['ZipFirstLetter']
        and 'ZipSecondLetter' in intent['slots'] and 'value' in intent['slots'] ['ZipSecondLetter']
        and 'HouseNumber' in intent['slots'] and 'value' in intent['slots'] ['HouseNumber']):

        zip_code = intent['slots']['ZipNumber']['value'] + intent['slots']['ZipFirstLetter']['value'] + intent['slots']['ZipSecondLetter']['value'] 
        house_number = intent['slots']['HouseNumber']['value'] 

        print("Getting when response for zip {} and house number {}".format(zip_code, house_number))

        # Scrape the pick up days from the website
        print("Retrieving HTML...")
        #html = '<div class="assemblySide"><div class="subBody"><div class="itemBlock"><h2>Eerstvolgende inzameldata</h2><ul class="listSmall"><li><img src="/HuisVuilFrontOffice/img/icon_papier.png" alt="Ophaaldag papier"><strong>Papier</strong><br>donderdag 30 juni</li></ul></div><div class="itemBlock"><h2>Legenda</h2><div class="textCnt"><ul class="listSmall"><li><img src="/HuisVuilFrontOffice/img/icon_papier.png" alt="Ophaaldag papier">Ophaaldag Papier</li></ul><br><a id="wt58_wt29" href="http://www.denhaag.nl/afval">Klik hier voor meer informatie over de verschillende soorten afval en het scheiden van uw huisvuil.</a></div></div></div></div>'
        html = HTMLLoader.get_html(zip_code, house_number)
       
        print("Parsing HTML...")
        parser = PickUpHTMLParser()
        parser.feed(html)

        data_pairwise = parser.get_data_pairwise()

        print("Translating data...")
        pick_up_days = []
        for type_dutch, date_dutch in data_pairwise:
            try:
                translated = PickUpTranslator.translate(type_dutch, date_dutch)
            except:
                translated = "Translation error"
            pick_up_days.append(translated)

        # Return the info
        speech_output = "The next pick up days for {} number {} are: {}".format(zip_code, house_number, ", ".join(pick_up_days))
        reprompt_text = ""
        should_end_session = True
    else:
        speech_output = "I didn't hear a Dutch zip code. Please try again."
        reprompt_text = "Ask me when your pick up days are by saying, " \
                    "when for two five six two x l."
        should_end_session = False
    return build_response({}, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

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
    
def log(str):
    #print str
    print(str)

class PickUpHTMLParser(HTMLParser):

    # TODO use instance variables
    in_inzameldata = False
    data = []

    def handle_endtag(self, tag):
        if tag == "ul":
            PickUpHTMLParser.in_inzameldata = False

    def handle_data(self, data):
        if PickUpHTMLParser.in_inzameldata:
            log("Encountered some data  :" + data)
            PickUpHTMLParser.data.append(data)
        if data == "Eerstvolgende inzameldata":
            log("in inzameldata")
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
        log("Traslating type '{}' and date '{}'".format(type_dutch, date_dutch))
        # Date Ex: donderdag 30 juni
        [dayofweek_dutch, numday, month_dutch] = date_dutch.split()
        translated = '{} on {}, {} {};'.format(
            PickUpTranslator.types[type_dutch.lower()], 
            PickUpTranslator.days[dayofweek_dutch.lower()], 
            PickUpTranslator.months[month_dutch.lower()] ,
            numday)
        log("Translated to: " + translated)
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