from flask import Flask, request, render_template
from sqlalchemy import create_engine, text

app = Flask(__name__)
#engine = create_engine("postgresql://gaoyb7@localhost/dht_demo")
#conn = engine.connect()

@app.route("/")
def index():
    return render_template("base.html")


@app.route("/search")
def search():
    kw = request.args.get("kw").strip()
    kw = ":* & ".join(kw.split()) + ":*"

    precheck_cmd = '''select to_tsquery('english', '%s')''' % kw
    r = conn.execute(precheck_cmd)
    print(precheck_cmd)
    if r.fetchone()[0] == "":
        return "None"

    cmd = '''select * from hash_tab where to_tsvector('english', name) @@ \
            to_tsquery('english', '%s')''' % kw
    r = conn.execute(cmd)
    counts = r.rowcount
    #page += "Magnet: " + to_magnet(item[0], item[1]) + "</br>"

    return render_template("search.html", match_torrents_count=counts, total_torrents=100)


def to_magnet(infohash, name):
    magnet = "magnet:?xt=urn:btih:" + infohash
    magnet += "&dn=" + name
    return magnet


def torrents_count():
    cmd = "select count(*) from hash_tab"
    r = conn.execute(cmd)
    for item in r:
        return item[0]


if __name__ == "__main__":
    app.template_folder = "simServer/templates"
    app.debug = True
    app.run(port=8080)
