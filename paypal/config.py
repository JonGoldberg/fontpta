"""Module for loading a paypal access token from disk so keys don't ever get checked in.

The config file should be of the format:

```
[DEFAULT]
APP_ID = APP-MYIDHERE
APP_CLIENT_ID = myclientid
APP_SECRET = myappsecret
```

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
        app_client_id = config['DEFAULT']['APP_CLIENT_ID'],
        app_secret = config['DEFAULT']['APP_SECRET'],
    )
