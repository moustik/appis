from flask import Flask
from flask import make_response

import flask

# pip install Flask-PyMongo
from flask.ext.pymongo import PyMongo


from flask import render_template

app = Flask(__name__)
app.secret_key = 'The dirty monkey eats bananas!'
app.config['MONGO_HOST'] = '127.0.0.1'
app.config['MONGO_PORT'] = 27017
app.config['MONGO_DBNAME'] = 'intranet'
mongo = PyMongo(app)


def safe_get_first(cursor):
    return cursor[0] if cursor.count() else None


@app.route('/')
def home_page():
    members = mongo.db.members.find({'_id': 150721942})
    members = mongo.db.members.find().sort([("nom", 1), ("prenom", 1)])

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


@app.route('/member/<_id>')
def member_page(_id=None):
    print(_id)
    member = mongo.db.members.find({'_id': int(_id)})
    if member.count():
        member = member[0]
    else:
        member = None

    inscription = safe_get_first(mongo.db.inscriptions.find({'member_id': int(_id)}))
    structure = safe_get_first(mongo.db.structures.find({'_id': member["structure"]}))
    fonction = safe_get_first(mongo.db.fonctions.find({'_id': member["fonction"]}))
    formations = mongo.db.formations.find({'member_id': int(_id)}).sort([('role', -1),('date', 1)])
    qualifications = mongo.db.qualifications.find({'member_id': int(_id)})
    diplomes = mongo.db.diplomes.find({'member_id': int(_id)})
    return render_template('member.html',
                           member=member,
                           inscription=inscription,
                           fonction=fonction,
                           structure=structure,
                           formations=formations,
                           qualifications=qualifications,
                           diplomes=diplomes,
    )


@app.route('/structure')
def structure_index():
    structures = mongo.db.structures.find({})
    structures.sort('_id', 1)
    return render_template('structures.html', title="Index des structures", structures=structures)

@app.route('/structure/<structure>')
def structure_page(structure=406950000):
    members = mongo.db.members.find({'structure': int(structure)}).sort([("prenom", 1), ("nom", 1)])
    structures = mongo.db.structures.find({'_id': int(structure)})
    if structures.count():
        structure = structures[0] # first one actually
        title = structure["name"]
    else:
        title = "Aucune structure trouvee"
        structure = None


    # pivot on member id
    formations = mongo.db.formations.aggregate([
        {"$match": {
            "member_id": { "$in": map(lambda m: m['_id'], members)},
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

    members.rewind()
    # pivot on member id
    diplomes = mongo.db.diplomes.aggregate([
        {"$match": {"member_id": { "$in": map(lambda m: m['_id'], members)}}},
        {"$group": {"_id": "$member_id", "diplomes": { "$push": {"name": "$$ROOT.name", "date": "$$ROOT.date"}}}}
    ])
    # make it a dict
    diplomes = dict(map(lambda i: (i['_id'], i['diplomes']), diplomes['result']))

    members.rewind()
    # pivot on member id
    qualifications = mongo.db.qualifications.aggregate([
        {"$match": {"member_id": { "$in": map(lambda m: m['_id'], members)}}},
        {"$group": {"_id": "$member_id", "qualifications": { "$push": {"name": "$$ROOT.name", "titular": "$$ROOT.titular"}}}}
    ])
    # make it a dict
    qualifications = dict(map(lambda i: (i['_id'], i['qualifications']), qualifications['result']))

    members.rewind()
    # pivot on member id
    inscriptions = mongo.db.inscriptions.find({"member_id": { "$in": map(lambda m: m['_id'], members)}})
    inscriptions = dict(map(lambda i: (i['member_id'], {"inscription_type": i["inscription_type"]}), inscriptions))

    members.rewind()
    return render_template('members.html', title=title,
                           members=members,
                           formations=formations,
                           qualifications=qualifications,
                           diplomes=diplomes,
                           inscriptions=inscriptions,
    )


import re

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

    # filter out member's _id upon data from other collections
    it = request_dict.iteritems()
    filtered = None # set(map(lambda m: m['member_id'], mongo.db[k].find(dict(v))))
    blacklist = set([])
    if(len(request_dict.keys())):
#        (k, v) = it.next()
#        print k
        for k, v in it:
            print v
            if k[0] == "!":
                for cond in v:
                    blacklist = blacklist.union(set(map(lambda m: m['member_id'], mongo.db[k[1:]].find(dict([cond])))))
#                blacklist = blacklist.union(set(map(lambda m: m['member_id'], mongo.db[k[1:]].find(dict(v)))))
            else:
                if filtered:
                    filtered = filtered.intersection(set(map(lambda m: m['member_id'], mongo.db[k].find(dict(v)))))
                else:
                    filtered = set(map(lambda m: m['member_id'], mongo.db[k].find(dict(v))))

    final_req.update({"_id": { "$nin": list(blacklist)}})

    # update final request with matching members' _id
    if filtered:
        final_req["_id"]["$in"] = list(filtered)

    print(final_req)

    members = mongo.db.members.find(final_req).sort([("prenom", 1), ("nom", 1)])

    # pivot on member id
    formations = mongo.db.formations.aggregate([
        {"$match": {
            "member_id": { "$in": map(lambda m: m['_id'], members)},
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
#    print(reduce(lambda s,i: s.union(set(i)), , set([])))
    formations_list = set([sub["name"] for item in formations.values() for sub in item])

    members.rewind()
    # pivot on member id
    diplomes = mongo.db.diplomes.aggregate([
        {"$match": {"member_id": { "$in": map(lambda m: m['_id'], members)}}},
        {"$group": {"_id": "$member_id", "diplomes": { "$push": {"name": "$$ROOT.name", "date": "$$ROOT.date"}}}}
    ])
    # make it a dict
    diplomes = dict(map(lambda i: (i['_id'], i['diplomes']), diplomes['result']))
    diplomes_list = set([sub["name"] for item in diplomes.values() for sub in item])

    members.rewind()
    # pivot on member id
    qualifications = mongo.db.qualifications.aggregate([
        {"$match": {"member_id": { "$in": map(lambda m: m['_id'], members)}}},
        {"$group": {"_id": "$member_id", "qualifications": { "$push": {"name": "$$ROOT.name", "titular": "$$ROOT.titular"}}}}
    ])
    # make it a dict
    qualifications = dict(map(lambda i: (i['_id'], i['qualifications']), qualifications['result']))
    qualifications_list = set([sub["name"] for item in qualifications.values() for sub in item])

    members.rewind()
    # pivot on member id
    inscriptions = mongo.db.inscriptions.find({"member_id": { "$in": map(lambda m: m['_id'], members)}})
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
#        r.headers["Content-Disposition"] = "attachment; filename=export.csv"
        r.headers["Content-type"] = "text/text"
    return r


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)