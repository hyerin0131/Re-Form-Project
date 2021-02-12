app = Flask(__name__)

app.config.from_object('config')
CORS(app, send_wildcard=True)

@app.route('/')
@cross_origin(supports_credentials=True)
def home():
    return 'test'

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5003, debug=True)