"""Module for loading a paypal access token from disk so keys don't ever get checked in.

The config file should be of the format:

```
[DEFAULT]
ACCESS_TOKEN = MY-ACCESS-TOKEN
APP_ID = APP-MYIDHERE
```

The access token and app id can be retrieved by making a paypal oauth2/token request like:
curl https://api.sandbox.paypal.com/v1/oauth2/token \
   -H "Accept: application/json" \
   -H "Accept-Language: en_US" \
   -u "ClientID:Secret" \
-d "grant_type=client_credentials"

with the ClientID and Secret retrieved from https://developer.paypal.com/developer/applications.

Note: the application must have `Transaction Search` enabled.
"""

from configparser import ConfigParser
from pathlib import Path
from os import path


def paypal_init(filename=None):
    """Load configuration variables from a filename.

    filename: Override the configuration file. Default to ~/.paypalconfig
    """
    if not filename:
        filename = path.join(Path.home(), '.paypalconfig')

    config = ConfigParser()
    config.read(filename)
    return dict(
        app_id=config['DEFAULT']['APP_ID'],
        access_token=config['DEFAULT']['ACCESS_TOKEN'],
    )
