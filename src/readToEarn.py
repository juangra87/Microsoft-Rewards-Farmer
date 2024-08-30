import logging
import random
import secrets
import time

from requests_oauthlib import OAuth2Session

from src.browser import Browser
from .activities import Activities
from .utils import Utils

client_id = '0000000040170455'
authorization_base_url = 'https://login.live.com/oauth20_authorize.srf'
token_url = 'https://login.microsoftonline.com/consumers/oauth2/v2.0/token'
redirect_uri = ' https://login.live.com/oauth20_desktop.srf'
scope = [ "service::prod.rewardsplatform.microsoft.com::MBI_SSL"]

class ReadToEarn:
    def __init__(self, browser: Browser):
        self.browser = browser
        self.webdriver = browser.webdriver
        self.activities = Activities(browser)

    def complete_read_to_earn(self):

        logging.info("[READ TO EARN] " + "Trying to complete Read to Earn...")

        account_name = self.browser.username

        # Should Really Cache Token and load it in.
        # To Save token
        #with open('token.pickle', 'wb') as f:
        #    pickle.dump(token, f)
        # To Load token
        #with open('token.pickle', 'rb') as f:
        #   token = pickle.load(f)
        #mobileApp = OAuth2Session(client_id, scope=scope, token=token)

        # Use Webdriver to get OAuth2 Token
        # This works, since you already logged into Bing, so no user interaction needed

        mobile_app = Utils.make_requests_session(OAuth2Session(client_id, scope=scope, redirect_uri=redirect_uri))
        authorization_url, _ = mobile_app.authorization_url(authorization_base_url, access_type="offline_access", login_hint=account_name)

        # Get Referer URL from webdriver
        self.webdriver.get(authorization_url)
        while True:
            logging.info("[READ TO EARN] Waiting for Login")
            if self.webdriver.current_url.startswith("https://login.live.com/oauth20_desktop.srf?code="):
                redirect_response = self.webdriver.current_url
                break
            time.sleep(1)

        logging.info("[READ TO EARN] Logged-in successfully !")
        # Use returned URL to create a token
        mobile_app.fetch_token(token_url, authorization_response=redirect_response, include_client_id=True)

        # Do Daily Check in
        json_data = {
            'amount': 1,
            'country': self.browser.locale_geo.lower(),
            'id': 1,
            'type': 101,
            'attributes': {
                'offerid': 'Gamification_Sapphire_DailyCheckIn',
            },
        }
        json_data['id'] = secrets.token_hex(64)
        logging.info("[READ TO EARN] Daily App Check In")
        r = mobile_app.post("https://prod.rewardsplatform.microsoft.com/dapi/me/activities",json=json_data)
        balance = r.json().get("response").get("balance")
        time.sleep(random.randint(10, 20))

        # json data to confirm an article is read
        json_data = {
            'amount': 1,
            'country': self.browser.locale_geo.lower(),
            'id': 1,
            'type': 101,
            'attributes': {
                'offerid': 'ENUS_readarticle3_30points',
            },
        }

        # 10 is the most articles you can read. Sleep time is a guess, not tuned
        for i in range(10):
            # Replace ID with a random value so get credit for a new article
            json_data['id'] = secrets.token_hex(64)
            r = mobile_app.post("https://prod.rewardsplatform.microsoft.com/dapi/me/activities",json=json_data)
            newbalance = r.json().get("response").get("balance")
            if newbalance == balance:
                logging.info("[READ TO EARN] Read All Available Articles !")
                break
            else:
                logging.info("[READ TO EARN] Read Article " + str(i+1))
                balance = newbalance
                time.sleep(random.randint(10, 20))

        logging.info("[READ TO EARN] Completed the Read to Earn successfully !")