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
    page = "Total torrent:  " + str(torrent_count()) + "</br>" + search_form
    page += "</br>"
    page += "Result: </br>"

    kw = request.args.get("kw").strip()
    if kw == "":
        return "None"

    kw = ":* & ".join(kw.split()) + ":*"

    precheck_cmd = '''select to_tsquery('english', '%s')''' % kw

    r = conn.execute(precheck_cmd)

    print(precheck_cmd)
    if r.fetchone()[0] == "":
        return "None"

    cmd = '''select * from hash_tab where to_tsvector('english', name) @@ \
            to_tsquery('english', '%s')''' % kw

    r = conn.execute(cmd)

    page = "Total torrents:  " + str(torrent_count()) + "</br>" + search_form
    page += "</br>"
    page += "Result: " + str(r.rowcount) + " items</br>"
    for item in r:
        page += "Name: " + item[1] + "</br>"
        page += "Magnet: " + to_magnet(item[0], item[1]) + "</br>"
        page += "</br>"
    return page


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
