from flask import Flask, url_for, request
from sqlalchemy import create_engine, text

app = Flask(__name__)

engine = create_engine("postgresql://gaoyb7@localhost/dht_demo")
conn = engine.connect()
search_form = \
    """
    <form method="GET" action="/search">
        <input id="kw" name="kw" />
        <button type="submit">search</button>
    </form>
    """

@app.route("/")
def main_page():
    return "Total torrents:  " + str(torrent_count()) + "</br>" + search_form


@app.route("/about")
def about():
    return "A simple Torrent Search Engine based on DHT protocol"


@app.route("/search")
def search():
    msg = "Total torrent:  " + str(torrent_count()) + "</br>" + search_form
    msg += "</br>"
    msg += "Result: </br>"

    name = request.args.get('kw')
    cmd = "select * from hash_tab where upper(name) like " + "'%" + name.upper() + "%'"
    r = conn.execute(text(cmd))
    for item in r:
        msg += "Name: " + item[1] + "</br>"
        msg += "Magnet: " + to_magnet(item[0], item[1]) + "</br>"
        msg += "</br>"
    return msg


def to_magnet(infohash, name):
    magnet = "magnet:?xt=urn:btih:" + infohash
    magnet += "&dn=" + name
    return magnet


def torrent_count():
    cmd = "select count(*) from hash_tab"
    r = conn.execute(cmd)
    for x in r:
        return x[0]



if __name__ == "__main__":
    app.debug = True
    app.run(host="0.0.0.0")
