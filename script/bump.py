"""Standalone WG-Gesucht advertisement bumper.

This is a self-contained script: it does NOT depend on the `core` package
and only requires the third-party `requests` library (`pip install requests`).

It bumps one or more advertisements to the top of their listing.
Bumping mirrors the behaviour of the Rust `wg_gesucht_updater` tool:
an advertisement is first deactivated and then activated again, which
moves it back to the top of the relevant listing.

An advertisement (offer) ID is the numeric part of its WG-Gesucht URL.

Authentication:
  The script needs a valid session. You can either
    - provide an existing `account.json` (see authExample.py), or
    - pass credentials via the WG_USERNAME / WG_PASSWORD environment variables
      (or the --username / --password command line options), and the script
      will log in for you (and cache the session to account.json).

Usage:
  python examples/bumpExample.py <offerId> [<offerId> ...]
  python examples/bumpExample.py --username you@mail.com --password secret 12345678

If no IDs are passed on the command line, the IDs in DEFAULT_OFFER_IDS
below are used instead.
"""

import argparse
import json
import os
import sys

import requests


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Fallback offer IDs used when none are given on the command line.
DEFAULT_OFFER_IDS = ['9403396', '8986669']

# Where the session (account) data is cached.
ACCOUNT_FILE = 'account.json'

# Endpoint that changes an advertisement's active state.
# PATCH https://www.wg-gesucht.de/api/offers/{offerId}/users/{userId}
OFFER_MODIFY_ENDPOINT = 'offers/{}/users/{}'

class WgGesuchtClient:
    """A trimmed-down WG-Gesucht API client with just what bumping needs."""

    # Constants
    API_URL = 'https://www.wg-gesucht.de/api/{}'
    APP_VERSION = '1.28.0'
    APP_PACKAGE = 'com.wggesucht.android'
    CLIENT_ID = 'wg_mobile_app'
    USER_AGENT = ('Mozilla/5.0 (Linux; Android 6.0; Google Build/MRA58K; wv) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 '
                  'Chrome/74.0.3729.186 Mobile Safari/537.36')

    def __init__(self):
        self.userId = None
        self.accessToken = None
        self.refreshTokenValue = None
        self.phpSession = None
        self.devRefNo = None

    def request(self, method, endpoint, params=None, payload=None, attempt=0):
        url = self.API_URL.format(endpoint)
        cookies = [
            'PHPSESSID={}'.format(self.phpSession) if self.phpSession else None,
            'X-Client-Id={}'.format(self.CLIENT_ID),
            'X-Refresh-Token={}'.format(self.refreshTokenValue) if self.refreshTokenValue else None,
            'X-Access-Token={}'.format(self.accessToken) if self.accessToken else None,
            'X-Dev-Ref-No={}'.format(self.devRefNo) if self.devRefNo else None,
        ]
        cookieHeader = '; '.join(cookie for cookie in cookies if cookie)
        headers = {
            'X-App-Version': self.APP_VERSION,
            'User-Agent': self.USER_AGENT,
            'Content-Type': 'application/json',
            'Accept-Encoding': 'gzip, deflate',
            'Accept': 'application/json',
            'X-Client-Id': self.CLIENT_ID,
            'X-Authorization': 'Bearer {}'.format(self.accessToken) if self.accessToken else None,
            'X-User-Id': self.userId if self.userId else None,
            'X-Dev-Ref-No': self.devRefNo if self.devRefNo else None,
            'Cookie': cookieHeader,
            'X-Requested-With': self.APP_PACKAGE,
            'Origin': 'file://' if not self.accessToken else None
        }
        r = requests.request(method=method, url=url, headers=headers,
                             params=params, data=payload)
        if r.status_code in range(200, 300):
            return r

        elif r.status_code == 401 and attempt < 1:
            if self.refreshToken():
                return self.request(method, endpoint, params, payload, attempt + 1)
            else:
                print('Refresh token request failed: {}'.format(r.text))
                return None

        else:
            print('Request failed: {}'.format(r.text))
            return None

    def importAccount(self, config):
        self.userId = config['userId']
        self.accessToken = config['accessToken']
        self.refreshTokenValue = config['refreshToken']
        self.phpSession = config['phpSession']
        self.devRefNo = config['devRefNo']

    def exportAccount(self):
        return {
            'userId': self.userId,
            'accessToken': self.accessToken,
            'refreshToken': self.refreshTokenValue,
            'phpSession': self.phpSession,
            'devRefNo': self.devRefNo
        }

    # Login
    def login(self, username, password):
        payload = {
            'login_email_username': username,
            'login_password': password,
            'client_id': self.CLIENT_ID,
            'display_language': 'de'
        }

        # Request api
        r = self.request('POST', 'sessions', None, json.dumps(payload))

        if not r:
            return False

        # Success, set data
        jsonBody = r.json()
        self.accessToken = jsonBody['detail']['access_token']
        self.refreshTokenValue = jsonBody['detail']['refresh_token']
        self.userId = jsonBody['detail']['user_id']
        self.devRefNo = jsonBody['detail']['dev_ref_no']

        # PHPSESSID may not be present on the final response; fall back
        # gracefully since auth is token-based.
        self.phpSession = r.cookies.get('PHPSESSID')
        if self.phpSession is None:
            for prev in r.history:
                if 'PHPSESSID' in prev.cookies:
                    self.phpSession = prev.cookies.get('PHPSESSID')
                    break
        return True

    # Refresh login token
    def refreshToken(self):

        # Build payload
        payload = {
            'grant_type': 'refresh_token',
            'access_token': self.accessToken,
            'refresh_token': self.refreshTokenValue,
            'client_id': self.CLIENT_ID,
            'dev_ref_no': self.devRefNo,
            'display_language': 'de'
        }

        # Build url
        url = 'sessions/users/{}'.format(self.userId)

        # Request api
        r = self.request('POST', url, None, json.dumps(payload))

        if not r:
            return False

        # Success, set new data
        jsonBody = r.json()
        self.accessToken = jsonBody['detail']['access_token']
        self.refreshTokenValue = jsonBody['detail']['refresh_token']
        self.devRefNo = jsonBody['detail']['dev_ref_no']
        return True


# ---------------------------------------------------------------------------
# Bumping logic
# ---------------------------------------------------------------------------

def setDeactivated(client, offerId, deactivated):
    """Sets whether an advertisement is deactivated.

    Returns True on success, False otherwise.
    """
    url = OFFER_MODIFY_ENDPOINT.format(offerId, client.userId)

    # Build payload. The API expects the flag as the string '1' or '0'.
    payload = {
        'deactivated': '1' if deactivated else '0'
    }
    r = client.request('PATCH', url, None, json.dumps(payload))

    # A truthy response object means the request succeeded.
    return r is not None


def deactivate(client, offerId):
    """Deactivates an advertisement."""
    return setDeactivated(client, offerId, True)


def activate(client, offerId):
    """Activates an advertisement."""
    return setDeactivated(client, offerId, False)


def bump(client, offerId):
    """Bumps an advertisement by deactivating and then activating it."""

    print('Bumping offer {}...'.format(offerId))

    # Deactivate first
    if not deactivate(client, offerId):
        print('  Failed to deactivate offer {}'.format(offerId))
        return False

    # Then activate again
    if not activate(client, offerId):
        print('  Failed to activate offer {}'.format(offerId))
        return False

    print('  Bumped offer {}'.format(offerId))
    return True


# ---------------------------------------------------------------------------
# Authentication helpers
# ---------------------------------------------------------------------------

def authenticate(client, username, password):
    """Prepares the client so it can talk to the API.

    Order of preference:
      1. Existing account.json session.
      2. Login with the supplied credentials (and cache the session).

    Returns True when the client is ready, False otherwise.
    """

    # 1. Try a cached session
    if os.path.exists(ACCOUNT_FILE):
        try:
            with open(ACCOUNT_FILE, 'r') as file:
                account = json.loads(file.read())
            client.importAccount(account)
            print('Loaded session from {}'.format(ACCOUNT_FILE))
            return True
        except (OSError, ValueError, KeyError) as e:
            print('Could not use {} ({}), falling back to login.'.format(ACCOUNT_FILE, e))

    # 2. Fall back to a fresh login
    if username and password:
        if client.login(username, password):
            print('Logged in as {}'.format(username))
            # Cache the session for next time
            try:
                with open(ACCOUNT_FILE, 'w') as file:
                    file.write(json.dumps(client.exportAccount()))
            except OSError as e:
                print('Warning: could not write {} ({})'.format(ACCOUNT_FILE, e))
            return True
        print('Login failed.')
        return False

    print('No {} found and no credentials provided.'.format(ACCOUNT_FILE))
    print('Set WG_USERNAME/WG_PASSWORD or pass --username/--password.')
    return False


def parseArgs():
    parser = argparse.ArgumentParser(
        description='Bump WG-Gesucht advertisements to the top of their listing.')
    parser.add_argument('offerIds', nargs='*',
                        help='Offer IDs to bump (numeric part of the ad URL).')
    parser.add_argument('--username', default=os.environ.get('WG_USERNAME'),
                        help='WG-Gesucht username/email (or set WG_USERNAME).')
    parser.add_argument('--password', default=os.environ.get('WG_PASSWORD'),
                        help='WG-Gesucht password (or set WG_PASSWORD).')
    return parser.parse_args()


def main():
    args = parseArgs()
    client = WgGesuchtClient()
    if not authenticate(client, args.username, args.password):
        sys.exit(1)
    offerIds = args.offerIds if args.offerIds else DEFAULT_OFFER_IDS

    failures = []
    for offerId in offerIds:
        if not bump(client, offerId):
            failures.append(offerId)

    if failures:
        print('Failed to bump: {}'.format(', '.join(failures)))
        sys.exit(1)

    print('Done.')


if __name__ == '__main__':
    main()
