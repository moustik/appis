import re
from datetime import date

from flask import Flask
from flask import make_response

import flask
import flask.json

# pip install Flask-PyMongo
from flask.ext.pymongo import PyMongo


from flask import render_template


PACKS = {
    # Lyon Levant
    0: [406950000],
    # Presqu'ile - USA Gandhi - 4 Chateaux - Gerland
    1: [406950600, 406951700, 406952300],
    # Sacre Coeur - Immac - Saint Nom - Nativite - Saint Eucher
    2: [406950700, 406950900, 406951200, 406951800, 406951000],
    # Saint Vincent - Saint Pothin - Charpennes - Saint Joseph - Meyzieu
    3: [406950800, 406951300, 406951900, 406951400, 406952100],
    # La Guillotiere - Genas Chassieu - Bron - Saint Priest
    4: [406951500, 406952400, 406952200],
    # autres
    5: [406953500],

}

MEMBER_PREPROJECTION = {"id": 1, "nom": 1, "prenom": 1,
                        "inscription_starts": 1, "inscription_type": 1,
                        "adresse": 1, "ville": 1, "date_de_naissance": 1,
                        "telephones_portables": 1,
                        "courriels": 1, "structure": 1, "fonction": 1}

MEMBER_PROJECTION = {"id": "$doc.id",
                     "nom": "$doc.nom",
                     "prenom": "$doc.prenom",
                     "adresse": "$doc.adresse",
                     "ville": "$doc.ville",
                     "date_de_naissance": "$doc.date_de_naissance",
                     "telephones_portables": "$doc.telephones_portables",
                     "courriels": "$doc.courriels",
                     "structure": "$doc.structure",
                     "fonction": "$doc.fonction"}

app = Flask(__name__)
app.secret_key = 'The dirty monkey eats bananas!'
app.config['MONGO_HOST'] = '127.0.0.1'
app.config['MONGO_PORT'] = 27017
app.config['MONGO_DBNAME'] = 'intranet'
mongo = PyMongo(app)


def safe_get_first(cursor):
    return cursor[0] if cursor.count() else None


@app.route('/index')
def home_page():
    members = mongo.db.members.find({'id': 150721942})
    members = mongo.db.members.find().sort([("nom", 1), ("prenom", 1)])
    members = mongo.db.members.aggregate(
        [
            {"$match": { "inscription_ends": { "$regex": ".*201[5678]"}, "inscription_type": 0}},
            {"$sort": { "timestamp": -1 }},
            {"$group": { "_id": "$id", "doc": { "$first": "$$ROOT" }}},
            {"$project": MEMBER_PROJECTION},
        ]
    )
    members = sorted(members["result"], key=lambda s: s["nom"])

    # pivot on member id
    formations = mongo.db.formations.aggregate([
        {"$match": {"role": "Stagiaire"}},
        {"$group": {"_id": "$member_id", "formations": { "$push": "$$ROOT" }}}
    ])
    # make it a dict
    formations = dict(map(lambda i: (i['_id'], i['formations']), formations['result']))

    # pivot on member id
    diplomes = mongo.db.diplomes.aggregate([
        {"$group": {"_id": "$member_id", "diplomes": { "$push": {"name": "$$ROOT.name", "date": "$$ROOT.date"}}}}
    ])
    # make it a dict
    diplomes = dict(map(lambda i: (i['_id'], i['diplomes']), diplomes['result']))

    # pivot on member id
    qualifications = mongo.db.qualifications.aggregate([
        {"$group": {"_id": "$member_id", "qualifications": { "$push": {"name": "$$ROOT.name", "titular": "$$ROOT.titular"}}}}
    ])
    # make it a dict
    qualifications = dict(map(lambda i: (i['_id'], i['qualifications']), qualifications['result']))

    inscriptions = mongo.db.inscriptions.find()
    inscriptions = dict(map(lambda i: (i['member_id'], {"inscription_type": i["inscription_type"]}), inscriptions))
    return render_template('members.html', title="Index des adherents",
                           members=members,
                           formations=formations,
                           qualifications=qualifications,
                           diplomes=diplomes,
                           inscriptions=inscriptions,
    )


import bson
from bson import json_util

@app.route('/data/member/<int:_id>')
@app.route('/member/<int:_id>')
def member_page(_id=None):
    member = mongo.db.members.find({'id': int(_id)})
    if member.count():
        member = member[member.count()-1]
    else:
        member = None

    inscription = safe_get_first(mongo.db.inscriptions.find({'member_id': int(_id)}))
    structure = safe_get_first(mongo.db.structures.find({'id': member["structure"]}))
    fonction = safe_get_first(mongo.db.fonctions.find({'id': member["fonction"]}))
    formations = mongo.db.formations.find({'member_id': int(_id)}).sort([('role', -1),('date', 1)])
    qualifications = mongo.db.qualifications.find({'member_id': int(_id)})
    diplomes = mongo.db.diplomes.find({'member_id': int(_id)})

    if flask.request.path.startswith("/data"):
#        return flask.json.jsonify({"n": 1, "result": {
        return flask.Response(
            flask.json.dumps(
                {"n": 1, "result": {
                    "member": member,
                    "inscription": inscription,
                    "fonction": fonction,
                    "structure": structure,
                    "formations": list(formations),
                    "qualifications": list(qualifications),
                    "diplomes": list(diplomes),
                }
             },
                default=json_util.default, indent=4, sort_keys=True
            ),
            mimetype='application/json', 
        )
    else:
        return render_template('member.html',
                               member=member,
                               inscription=inscription,
                               fonction=fonction,
                               structure=structure,
                               formations=formations,
                               qualifications=qualifications,
                               diplomes=diplomes,
                           )


@app.route('/')
@app.route('/structure')
def structure_index():
    structures = mongo.db.structures.aggregate(
        [
            {"$sort": { "timestamp": -1 }},
            {"$group": { "_id": "$id", "doc": { "$first": "$$ROOT" }}},
            {"$project": {"id": "$doc.id", "name": "$doc.name", "headcount": "$doc.headcount"}},
        ]
    )
    struct2pack = dict([ (ss/100, p) for p, k in PACKS.iteritems() for ss in k ])
    structures = sorted(sorted(structures["result"], key=lambda s: s["id"]),
                        key=lambda s: struct2pack[s["id"]/100])
    def add_pack_id(s):
        s["pack"] = struct2pack[s["id"]/100]
        return s

    structures = map(add_pack_id, structures)
    return render_template('structures.html', title="Index des structures", structures=structures)


@app.route('/structure/<structure>')
def structure_page(structure=406950000):
    members = mongo.db.members.aggregate(
        [
            {"$match": {'structure': int(structure),
                        "inscription_starts": { "$regex": ".*201[5678]"},
                        "inscription_type": 0}},
            {"$sort": { "timestamp": -1 }},
            {"$group": { "_id": "$id", "doc": { "$first": "$$ROOT" }}},
            {"$project": MEMBER_PROJECTION},
        ]
    )
    members = sorted(members["result"], key=lambda s: s["prenom"])

    structures = mongo.db.structures.find({'id': int(structure)})
    if structures.count():
        structure = structures[0] # first one actually
        title = structure["name"]
    else:
        title = "Aucune structure trouvee"
        structure = None

    formations, qualifications, diplomes, inscriptions = get_side_data(members)

    return render_template('members.html', title=title,
                           members=members,
                           formations=formations,
                           qualifications=qualifications,
                           diplomes=diplomes,
                           inscriptions=inscriptions,
                           is_structure=True,
    )

@app.route('/overview/<structure>')
def structure_overview_page(structure=406950000):
    projX = MEMBER_PREPROJECTION.copy()
    projX.update(
        {"parent_structure":  {
            "$subtract": [
                {"$divide": ["$structure", 100]},
                {"$mod": [{"$divide": ["$structure", 100]}, 1]}
            ]
        }
     })
    members = mongo.db.members.aggregate(
        [
            {"$project": projX},
            {"$match": { "parent_structure": int(structure)/100,
                        "inscription_starts": { "$regex": ".*201[5678]"},
                        "inscription_type": 0}},
            {"$sort": { "timestamp": -1 }},
            {"$group": { "_id": "$id", "doc": { "$first": "$$ROOT" }}},
            {"$project": MEMBER_PROJECTION},
            {"$sort": { "fonction": 1, "structure": 1 }},
        ]
    )
    members = members["result"]

    structure = mongo.db.structures.find_one({'id': int(structure)/100*100})
    if structure:
        title = structure["name"]
    else:
        title = "Aucune structure trouvee"

    formations, qualifications, diplomes, inscriptions = get_side_data(members)

    structures = mongo.db.structures.aggregate(
        [
            {"$sort": { "timestamp": -1 }},
            {"$group": { "_id": "$id", "doc": { "$first": "$$ROOT" }}},
            {"$project": {"id": "$doc.id", "name": "$doc.name", "headcount": "$doc.headcount"}},
        ]
    )
    structures = sorted(structures["result"], key=lambda s: s["id"])
    structures = dict([(s["id"], {'name': " ".join(s["name"].split(" ")[1:]),
                                  'headcount': s["headcount"]}) for s in structures])

    return render_template('member_overview.html', title=title,
                           members=members,
                           formations=formations,
                           qualifications=qualifications,
                           diplomes=diplomes,
                           inscriptions=inscriptions,
                           structures=structures,
                           is_structure=False,
    )


def get_side_data(members):
    # pivot on member id
    formations = mongo.db.formations.aggregate([
        {"$match": {
            "member_id": { "$in": map(lambda m: m['id'], members)},
            "role": "Stagiaire"}},
        {"$group": {"_id": "$member_id", "formations": { "$push":
                                                         {"name": "$$ROOT.name",
                                                          "role": "$$ROOT.role",
                                                          "date": "$$ROOT.date"}
                                                       }
                  }}
    ])
    # make it a dict
    formations = dict(map(lambda i: (i['_id'], i['formations']), formations['result']))

    # pivot on member id
    diplomes = mongo.db.diplomes.aggregate([
        {"$match": {"member_id": { "$in": map(lambda m: m['id'], members)}}},
        {"$group": {"_id": "$member_id", "diplomes": { "$push": {"name": "$$ROOT.name", "date": "$$ROOT.date"}}}}
    ])
    # make it a dict
    diplomes = dict(map(lambda i: (i['_id'], i['diplomes']), diplomes['result']))

    # pivot on member id
    qualifications = mongo.db.qualifications.aggregate([
        {"$match": {"member_id": { "$in": map(lambda m: m['id'], members)}}},
        {"$group": {"_id": "$member_id", "qualifications": { "$push": {"name": "$$ROOT.name", "titular": "$$ROOT.titular"}}}}
    ])
    # make it a dict
    qualifications = dict(map(lambda i: (i['_id'], i['qualifications']), qualifications['result']))

    # pivot on member id
    inscriptions = mongo.db.inscriptions.find({"member_id": { "$in": map(lambda m: m['id'], members)}})
    inscriptions = dict(map(lambda i: (i['member_id'], {"inscription_type": i["inscription_type"]}), inscriptions))

    return formations, qualifications, diplomes, inscriptions


def parse_and_set_type(s):
    (t, v) = s.split(":")
    return int(v) if t == "i" else v

@app.route('/request/<fmt>/<path:req>')
def request(fmt, req):
    item_list = req.split("/")
    request_list = map(lambda i: re.split(r"[=.]", i), item_list)
    request_dict = reduce(lambda d,b:
                          d.update(
                              { b[0]:
                                d.get(b[0], []) + [(b[1], parse_and_set_type(b[2]))]
                            })
                          or d,
                          request_list, {})
    title = "%s" % request_dict

    # request in member collection
    final_req = dict(request_dict.pop("members")) if "members" in request_dict  else {}

    # filter out member's id upon data from other collections
    it = request_dict.iteritems()
    filtered = None # set(map(lambda m: m['member_id'], mongo.db[k].find(dict(v))))
    blacklist = set([])
    if(len(request_dict.keys())):
        for k, v in it:
            print v
            if k[0] == "!":
                for cond in v:
                    blacklist = blacklist.union(set(map(lambda m: m['member_id'], mongo.db[k[1:]].find(dict([cond])))))
                blacklist = blacklist.union(set(map(lambda m: m['member_id'], mongo.db[k[1:]].find(dict(v)))))
            else:
                if filtered:
                    filtered = filtered.intersection(set(map(lambda m: m['member_id'], mongo.db[k].find(dict(v)))))
                else:
                    filtered = set(map(lambda m: m['member_id'], mongo.db[k].find(dict(v))))

    final_req.update({"id": { "$nin": list(blacklist)}})

    # update final request with matching members' id
    if filtered:
        final_req["id"]["$in"] = list(filtered)

    members = mongo.db.members.find(final_req).sort([("prenom", 1), ("nom", 1)])

    # pivot on member id
    formations = mongo.db.formations.aggregate([
        {"$match": {
            "member_id": { "$in": map(lambda m: m['id'], members)},
            "role": "Stagiaire"}},
        {"$group": {"_id": "$member_id", "formations": { "$push":
                                                         {"name": "$$ROOT.name",
                                                          "role": "$$ROOT.role",
                                                          "date": "$$ROOT.date"}
                                                       }
                  }}
    ])
    # make it a dict
    formations = dict(map(lambda i: (i['_id'], i['formations']), formations['result']))
    formations_list = set([sub["name"] for item in formations.values() for sub in item])

    members.rewind()
    # pivot on member id
    diplomes = mongo.db.diplomes.aggregate([
        {"$match": {"member_id": { "$in": map(lambda m: m['id'], members)}}},
        {"$group": {"_id": "$member_id", "diplomes": { "$push": {"name": "$$ROOT.name", "date": "$$ROOT.date"}}}}
    ])
    # make it a dict
    diplomes = dict(map(lambda i: (i['_id'], i['diplomes']), diplomes['result']))
    diplomes_list = set([sub["name"] for item in diplomes.values() for sub in item])

    members.rewind()
    # pivot on member id
    qualifications = mongo.db.qualifications.aggregate([
        {"$match": {"member_id": { "$in": map(lambda m: m['id'], members)}}},
        {"$group": {"_id": "$member_id", "qualifications": { "$push": {"name": "$$ROOT.name", "titular": "$$ROOT.titular"}}}}
    ])
    # make it a dict
    qualifications = dict(map(lambda i: (i['_id'], i['qualifications']), qualifications['result']))
    qualifications_list = set([sub["name"] for item in qualifications.values() for sub in item])

    members.rewind()
    # pivot on member id
    inscriptions = mongo.db.inscriptions.find({"member_id": { "$in": map(lambda m: m['id'], members)}})
    inscriptions = dict(map(lambda i: (i['member_id'], {"inscription_type": i["inscription_type"]}), inscriptions))

    members.rewind()
    r = make_response(render_template('members.%s' % fmt, title=title,
                                      members=members,
                                      formations=formations,
                                      qualifications=qualifications,
                                      diplomes=diplomes,
                                      inscriptions=inscriptions,
                                      formations_list=formations_list,
                                      qualifications_list=qualifications_list,
                                      diplomes_list=diplomes_list,
                                  ))
    if fmt == "csv":
        r.headers["Content-Disposition"] = "attachment; filename=export.csv"
        r.headers["Content-type"] = "text/text"
    return r


@app.route('/data/<structure>')
def data_structure(structure):
    structures = mongo.db.structures.find({"id": int(structure)}, {"_id": 0}).sort("timestamp")
    structures = filter(lambda s: s["headcount"][0] > 6, structures)
    return flask.json.jsonify({"res": list(structures)})


@app.route('/data/', defaults={"structure": {"$exists" : True}})
@app.route('/data/<int:structure>/members')
def data_structure_members(structure):
    members = mongo.db.members.aggregate(
        [
            {"$match": {'structure': structure,
                        "inscription_starts": { "$regex": ".*201[5678]"},
                        "inscription_type": 0}},
            {"$sort": { "timestamp": -1 }},
            {"$group": { "_id": "$id", "doc": { "$first": "$$ROOT" }}},
            {"$project": MEMBER_PROJECTION},
        ]
    )
    members = list(members["result"])
    return flask.json.jsonify({"n": len(members), "result": members})


def is_it_birthday(member, at=date.today()):
    born = date(*map(int, reversed(member["date_de_naissance"].split("/"))))
    return ((at.month, at.day) == (born.month, born.day))


@app.route('/data/birthdays')
@app.route('/view/birthdays')
def data_birthdays():
    members = mongo.db.members.aggregate(
        [
            {"$match": {
                "inscription_starts": { "$regex": ".*201[5678]"},
                "inscription_type": 0
                                  }},
            {"$sort": { "timestamp": -1 }},
            {"$group": { "_id": "$id", "doc": { "$first": "$$ROOT" }}},
            {"$project": MEMBER_PROJECTION},
        ]
    )

    fmembers = filter(lambda m: is_it_birthday(m, date.today()), members["result"])

    context = flask.request.path.split("/")[1]
    if context == "view":
        return render_template('members.html', title="Anniversaires",
                               members=fmembers,
                               formations=[],
                               qualifications=[],
                               diplomes=[],
                               inscriptions=[],
                           )
    elif context == "data":
        return flask.json.jsonify({"n": len(fmembers), "result": fmembers})


def age_from_member(member, at=date.today()):
    born = date(*map(int, reversed(member["date_de_naissance"].split("/"))))
    return (at.year - born.year - ((at.month, at.day) < (born.month, born.day)))


@app.route('/data/younglings')
@app.route('/view/younglings')
def data_younglings():
    members = mongo.db.members.aggregate(
        [
            {"$match": {
                "inscription_starts": { "$regex": ".*201[5678]"},
                "inscription_type": 0
#                "date_de_naissance": {"$gte": "ISODate('1998-01-01T00:00:00.0Z')"}
                                  }},
            {"$sort": { "timestamp": -1 }},
            {"$group": { "_id": "$id", "doc": { "$first": "$$ROOT" }}},
            {"$project": MEMBER_PROJECTION},
        ]
    )

    fmembers = filter(lambda m: age_from_member(m, date(2016, 7, 1)) < 18, members["result"])

    context = flask.request.path.split("/")[1]
    if context == "view":
        return render_template('members.html', title="Mineurs au 1er juillet 2016",
                               members=fmembers,
                               formations=[],
                               qualifications=[],
                               diplomes=[],
                               inscriptions=[],
                           )
    elif context == "data":
        return flask.json.jsonify({"n": len(fmembers), "result": fmembers})


from itertools import groupby

@app.route('/data/packed')
def data_packed():
    members = mongo.db.members.aggregate(
        [
            {"$match": {
                "inscription_starts": { "$regex": ".*201[5678]"},
                "inscription_type": 0
#                "date_de_naissance": {"$gte": "ISODate('1998-01-01T00:00:00.0Z')"}
                                  }},
            {"$sort": { "timestamp": -1 }},
            {"$group": { "_id": "$id", "doc": { "$first": "$$ROOT" }}},
            {"$project": MEMBER_PROJECTION},
        ]
    )

    structures = mongo.db.structures.aggregate(
        [
            {"$sort": { "timestamp": -1 }},
            {"$group": { "_id": "$id", "doc": { "$first": "$$ROOT" }}},
            {"$project": {"id": "$doc.id", "name": "$doc.name"}},
        ]
    )
    structures = sorted(structures["result"], key=lambda s: s["id"])
    structures = dict([(s["id"], " ".join(s["name"].split(" ")[1:])) for s in structures])
#    print(structures)

    fmembers = sorted(members["result"], key=lambda m: m["structure"])

    fmembers = groupby(fmembers, lambda m: m["structure"])
    fmembers = [ {"structure": k, "name": 0, "children": list(map(lambda m: {"name": m["prenom"]}, s))} for (k, s) in fmembers ]
    for s in fmembers:
        s["name"] = len(s["children"])

    fmembers = groupby(fmembers, lambda m: m["structure"]/100)
    fmembers = [ {"structure": -1, "name": structures[int(k*100)], "children": list(s)} for (k, s) in fmembers ]

    fmembers = {"structure": 0, "name": "", "children": fmembers }
    return flask.json.jsonify({"n": len(fmembers), "result": fmembers})


@app.route('/charts')
def charts():
    return render_template('charts/sunburst.html')


import datetime

@app.route('/last')
def last_logs():
    # > yesterday midnight
    starting = datetime.datetime.combine(
        datetime.date.today() - datetime.timedelta(days=1),
        datetime.time(0, 0))
    last = []
    for c in [
            mongo.db.diplomes,
            mongo.db.structures,
            mongo.db.formations,
            mongo.db.inscriptions,
            mongo.db.members,
            mongo.db.qualifications,
            mongo.db.structures,
    ]:                                     # > yesterday midnigth

        last += list(c.find({"timestamp": {"$gt": starting}},
                            {"_id": 0}))

    return flask.json.jsonify({"from": starting, "result": list(last)})


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
