import logging
import geofabric._config as config
from flask import Flask
import pyldapi
from geofabric.controller import classes, pages

app = Flask(__name__, template_folder=config.TEMPLATES_DIR, static_folder=config.STATIC_DIR)
app.register_blueprint(pages.pages)
app.register_blueprint(classes.classes)


# run the Flask app
if __name__ == '__main__':
    logging.basicConfig(filename=config.LOGFILE,
                        level=logging.DEBUG,
                        datefmt='%Y-%m-%d %H:%M:%S',
                        format='%(asctime)s %(levelname)s %(filename)s:%(lineno)s %(message)s')
    pyldapi.setup(app, config.APP_DIR, str(config.URI_BASE).rstrip('/'))
app.run(debug=config.DEBUG, threaded=True, use_reloader=False)
