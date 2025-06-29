import flask

app = flask.Flask(__name__)

@app.route('/')
def index():
    return flask.render_template('basepage.html')

@app.route('/about')
def about():
    return flask.render_template('basepage.html')

@app.route('/_/')
def mockup():
    return flask.render_template('mockup.html')

if __name__ == "__main__":
    app.run(debug=True)