from flask import Flask, url_for
from sqlalchemy import create_engine, text

app = Flask(__name__)

engine = create_engine("postgresql://gaoyb7@localhost/dht")
conn = engine.connect()

@app.route("/")
def hello_world():
    return "Hello World!"


@app.route("/about")
def about():
    return "A simple Torrent Search Engine based on DHT protocol"

@app.route("/search/<name>")
def search(name):
    cmd = "select * from hash_tab where upper(name) like " + "'%" + name.upper() + "%'"
    r = conn.execute(text(cmd))
    msg = ""
    for item in r:
        msg += "Name: " + item[1] + "</br>"
        msg += "Magnet: " + to_magnet(item[0], item[1]) + "</br>"
        msg += "</br>"
    return msg


def to_magnet(infohash, name):
    magnet = "magnet:?xt=urn:btih:" + infohash
    magnet += "&dn=" + name
    return magnet

if __name__ == "__main__":
    app.debug = True
    app.run(host="0.0.0.0")
