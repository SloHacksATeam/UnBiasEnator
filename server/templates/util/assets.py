from flask_assets import Bundle, Environment
from ... import app
bundles = {
    'images': Bundle(
        'img/bryce_slohacks.jpg',
        'img/sun_slohacks.jpg',
        'img/spencer_slohacks',
        output = 'gen/img'
        )

}

assets = Environment(app)
assets.register(bundles)