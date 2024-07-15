import json
import os

import firebase_admin
from fastapi_poe import make_app
from firebase_admin import credentials, db
from modal import Image, Secret, Stub, asgi_app

from CDSModelBot import CDSModelBot

image = Image.debian_slim().pip_install_from_requirements("requirements.txt")
stub = Stub("CDS-Generator-app")


@stub.function(image=image, secrets=[Secret.from_name("CDS-Generator-app")])
@asgi_app()
def fastapi_app():
    cred = credentials.Certificate(json.loads(os.environ["FIREBASE_KEY_JSON"]))
    firebase_admin.initialize_app(
        cred, {"databaseURL": "https://cap-project-99fb5-default-rtdb.europe-west1.firebasedatabase.app/"}
    )

    bot = CDSModelBot()
    app = make_app(bot, access_key=os.environ["POE_ACCESS_KEY"])
    return app
