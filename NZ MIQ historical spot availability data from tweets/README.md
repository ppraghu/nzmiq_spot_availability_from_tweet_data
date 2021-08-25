# NZ MIQ historical spot availability data from tweets
This folder contains a Python script that can pull historic tweets on NZ MIQ availability data from the twitter handle @allmiqdates.

To run this script, you need to have the Twitter Developer API key & secret key which you add inside the script where you see the following lines:

apiKey = "xyz"; # Enter the Twitter developer API Key
apiSecretKey = "abc"; # Enter the Twitter developer API Secret Key


## Outputs

This script generates 3 files:
* nzmiq_spot_availability_data.csv
* nzmiq_spot_availability_tweet_data.log
* error.log

The CSV file (the first one above) is the most valuable output which contains the slot availability data in a Comma-separated format which can be copied and pasted in an Excel sheet to create useful charts. An example Excel sheet containing different charts is also provided in this directory (nzmiq_spot_availability_data.xlsx).

The second file contains the raw tweets text. In case anyone wants any different analysis to be done, the raw data is available in this file.

The third file is just a report of errors encountered, such as Twitter API call failures and date format conversion errors.

## Constraints
* The Twitter "tweets" API allows to fetch only 3200 most recent Tweets (https://developer.twitter.com/en/docs/twitter-api/tweets/timelines/api-reference/get-users-id-tweets). Therefore, the output CSV file will contain the slot availability info of only about this many slots.

* Some of the slot availability tweets contain ranges of dates/months. At present, the tweet text parsing logic does not parse those tweets. But there are not many such tweets.
