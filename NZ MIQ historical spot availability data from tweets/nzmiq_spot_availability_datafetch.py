import sys
import base64
import json
import pytz
import logging
from datetime import datetime
from dateutil import parser
import requests
from playsound import playsound 
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning);

apiKey = "xyz"; # Enter the Twitter developer API Key
apiSecretKey = "abc"; # Enter the Twitter developer API Secret Key


urlBase = "https://api.twitter.com";
#
# URL to login and fetch the Bearer token
#
oauthURL = urlBase + "/oauth2/token";
#
# URL to fetch 10 tweet records of a given user.
# Note: The 1362206156546957312 below is the user id 
# of the username "allmiqdates".
#
tweetsURL = urlBase + "/2/users/1362206156546957312/tweets?" \
    + "tweet.fields=id,created_at,text";

csvLogger = None;
tweetDumpLogger = None;
errorLogger = None;

def setupLogger(name, logFile, format=None, consoleOutput=sys.stdout):
    fileHandler = logging.FileHandler(logFile, mode='w');
    consoleLogHandler = logging.StreamHandler(consoleOutput);
    if (format is not None):
        fileHandler.setFormatter(logging.Formatter(format));
        consoleLogHandler.setFormatter(logging.Formatter(format))
    logger = logging.getLogger(name);
    logger.setLevel(logging.INFO);

    # The logger will have a file to write the outputs
    logger.addHandler(fileHandler);

    # The logger also writes the output to console (stdout or stderr)
    logger.addHandler(consoleLogHandler);
    return logger

def configureLogging():
    global csvLogger, tweetDumpLogger, errorLogger;
    #
    # Create a CSV file that contains the details of
    # a given slot availability as per the tweet.
    #
    csvLogger = setupLogger("csvLogger",
        "nzmiq_spot_availability_data.csv");
    #
    # Create a log file that dumps all tweet texts
    # as obtained from Twitter's tweet API.
    #
    tweetDumpLogger = setupLogger("tweetDumpLogger",
        "nzmiq_spot_availability_tweet_data.log");
    #
    # Create a log file to write any errors such as
    # Twitter API errors and date parsing errors.
    #
    errorLogger = setupLogger("errorLogger",
        "error.log", "%(asctime)s %(levelname)s %(message)s", sys.stderr);

def get_bearer_token():
    keyWithSecret = apiKey + ":" + apiSecretKey;
    base64KeyWithSecret = base64.b64encode(keyWithSecret.encode('utf-8'));
    headers = {
        "Authorization": "Basic " + base64KeyWithSecret.decode('utf-8'),
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
    };
    response = requests.post(oauthURL, verify=False, headers=headers,
        data={'grant_type': 'client_credentials'})
    jsonResponse = json.dumps(response.json());
    data = json.loads(jsonResponse);
    tokenType = data['token_type']
    bearerToken = data['access_token'];
    return bearerToken;

def get_tweets(bearerToken):
    headers = {"Authorization": "Bearer {}".format(bearerToken)}
    #
    # At a time, the twitter tweets API returns only 10 tweets.
    # It also returns a pagination token for next set of records.
    # The nextToken variable is used to store the pagination token
    # returned.
    #
    nextToken = None;
    
    theUrl = tweetsURL;
    
    # Print the header row of the output CSV file
    csvLogger.info("Tweet CreatedDate (UTC) JSON String,"
        + "Date in which the Slot Appeared,"
        + "Day of Week,Time (NZ TZ),"
        + "Slot Date,"
        + "Number of Days for Travel Prepare");
    for count in range(500):
        if (nextToken != None):
            theUrl = tweetsURL + "&pagination_token=" + nextToken;
        try:
            response = requests.get(theUrl, verify=False, headers=headers);
        except:
            errorLogger.warning("Count " + str(count) 
                + " - Unexpected error for URL: "
                + theUrl + ": " + str(sys.exc_info()[0]));
            continue;
        jsonResponse = json.dumps(response.json());
        jsonResponse = json.loads(jsonResponse);
        meta = jsonResponse['meta'];
        nextTokenKey = 'next_token';
        if (nextTokenKey not in meta):
            break;
        nextToken = meta[nextTokenKey];
        #tweetDumpLogger.info("Counter: " + str(count));
        #tweetDumpLogger.info("nextToken = " + nextToken);
        dataKey = 'data';
        if (dataKey not in jsonResponse):
            break;
        tweetRecords = jsonResponse['data'];
        for tweetRecord in tweetRecords:
            tweetDumpLogger.info(tweetRecord);
            creationDateUTCTimeStr = tweetRecord['created_at'];
            text = tweetRecord['text'];
            #
            # The tweet containing the available slot starts
            # with "". E.g.:
            # Appeared at 9:09pm:\nSunday 8 August\nTuesday 19 October
            #
            if (text.startswith('Appeared at ') == False):
                continue;
            # The tweet text may have one slot or many slots
            # seperated by '\n'. Gather all of these into an
            # array.
            textTokens = text.split('\n');
            first = True;
            #
            # Logic to convert the created_time from UTC tz to
            # NZ tz. Not clear if this conversion accounts for
            # daylight saving, but it is just a one hour adjustment
            # which can be neglected, in the grand scheme of things.
            #
            nzTZ = pytz.timezone('Pacific/Auckland');
            creationDateUTCTime = parser.isoparse(creationDateUTCTimeStr);
            creationDateNZTTime = creationDateUTCTime.astimezone(nzTZ);
            creationDate = creationDateNZTTime.strftime("%m/%d/%Y");
            creationDayOfWeek = creationDateNZTTime.strftime("%A");
            creationTime = creationDateNZTTime.strftime("%H:%M");
            for textToken in textTokens: # One token is one available slot
                if first:
                    # The first token will be "Appeared at <time>:"
                    # Ignore this.
                    first = False;
                    continue;
                    
                # Expected slot time in this example format:
                # Sunday 8 August
                # Ignore the week day, gather the date & month
                # and append the year (assumed to be 2021.
                availableSlotDate = textToken.split(' ', 1)[1] + " 2021";
                try:
                    #
                    # Logic:
                    # Convert the date string to a datetime object
                    # Change the time zone to NZ TZ
                    # Convert this date into mm/dd/yyyy for Excel to understand 
                    # (assuming the Excel is set in the US date format)
                    # Also, find the difference between the date of 
                    # MIQ slot availability and the tweet date. 
                    # This is the number of days we get to travel to NZ
                    # and start MIQ.
                    #
                    availableSlotDateObj = \
                        datetime.strptime(availableSlotDate, '%d %B %Y');
                    availableSlotDateObj = \
                        availableSlotDateObj.replace(tzinfo=nzTZ)
                    availableSlotDate = \
                        availableSlotDateObj.strftime("%m/%d/%Y");
                    daysDifference = \
                        (availableSlotDateObj - creationDateNZTTime).days + 1;

                    # Print one slot availability data to the output CSV file
                    csvLogger.info(creationDateUTCTimeStr + "," 
                        + creationDate + "," 
                        + creationDayOfWeek + "," 
                        + creationTime + "," 
                        + availableSlotDate + ","
                        + str(daysDifference));
                except:
                    # At present, this script ignores a date range when
                    # appeared in the tweet text. Examples:
                    #   13-14 September
                    #   16 September - 30 November
                    # These will give parse error and we catch it for now.
                    errorLogger.warning("Count " + str(count) 
                        + " - Unexpected error for tweetRecord text: "
                        + text + ": " + str(sys.exc_info()[0]));
                    pass

def main():
    configureLogging();
    bearerToken = get_bearer_token();
    get_tweets(bearerToken);

if __name__== "__main__":
    main();
