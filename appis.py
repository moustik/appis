import sys

import requests
import pandas
from bs4 import BeautifulSoup
import StringIO

LOGIN_URL = "https://intranet.sgdf.fr"
EXTRACT_URL = "https://intranet.sgdf.fr/Specialisation/Sgdf/Adherents/ExtraireAdherents.aspx"
EFFECTIF_URL = "https://intranet.sgdf.fr/Specialisation/Sgdf/Pilotage/Adherents/EffectifTotalCategorieSexe.aspx"

HEADERS = {
    'User-Agent': "Mozilla/5.0 (Windows NT 6.1; rv:31.0) Gecko/20100101 Firefox/31.0",
    'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    'Accept-Language': 'fr,fr-fr;q=0.8,en-us;q=0.5,en;q=0.3',
}

COULEURS = {"21*": "orange",
    "22*": "bleu",
    "23*": "rouge",
    "24*": "vert",
    "27*": "farfa",
    }

viewstate = None

def init_session(s, login, password):
    r = s.get(LOGIN_URL, verify=True )\

    # parse and retrieve two vital form values
    soup = BeautifulSoup(r.text)
    viewstate = soup.select("#__VIEWSTATE")[0]['value']
    eventvalidation = soup.select("#__EVENTVALIDATION")[0]['value']\

    formdata = {
        '__EVENTVALIDATION': eventvalidation,
        '__EVENTTARGET': '',
        '__EVENTARGUMENT': '',
        '__VIEWSTATE': viewstate,
        '__VIEWSTATEGENERATOR': 'F4403698',
        "ctl00$MainContent$login":login,
        "ctl00$MainContent$password": password,
        "ctl00$MainContent$_btnValider": "Se connecter",
        "eo_version": "11.0.20.2",
        "eo_style_keys": "/wFk",
    }\

    r = s.post(LOGIN_URL, data=formdata, verify=True, headers=HEADERS, allow_redirects=True )
    print("Se connecter" not in r.text.encode('utf-8'))

def get_viewstate(s, url):
    # get form data
    r = s.get(url)\

    soup = BeautifulSoup(r.text)
    # parse and retrieve vital form value
    viewstate = soup.select("#__VIEWSTATE")[0]['value']
    return viewstate

def extraire_chefs(s, viewstate, codes_chefs):
    formdata = {
        '__EVENTTARGET': '',
        '__EVENTARGUMENT': '',
        '__VIEWSTATE': viewstate,
        '__VIEWSTATEGENERATOR': 'F4403698',
        "ctl00$MainContent$_selecteur$_tbCode": "",
        "ctl00$MainContent$_tbCodesFonctions": codes_chefs,
        "ctl00$MainContent$_ddCategorieMembre":-1,
        "ctl00$MainContent$_ddTypeInscription": -1,
        "ctl00$MainContent$_ddSpecialite":-1,
        "ctl00$MainContent$_ddTypeContact":-1,
        "ctl00$MainContent$_ddDiplome":-1,
        "ctl00$MainContent$_ddQualification":-1,
        "ctl00$MainContent$_ddFormation":-1,
        "ctl00$MainContent$_ddRevue":-1,
        "ctl00$MainContent$_ddMailInfoMouv":-1,
        "ctl00$MainContent$_ddMailInfoExt":-1,
        "ctl00$MainContent$_cbExtraireIndividu": "on",
        "ctl00$MainContent$_cbExtraireInscription": "on",
        "ctl00$MainContent$_btnExporter.x":50,
        "ctl00$MainContent$_btnExporter.y":7,
    }\

    r = s.post(EXTRACT_URL, data=formdata, headers=HEADERS)
    print(r.headers['content-type'])
    xls_file = StringIO.StringIO(r.text.encode("utf-8"))
    chefs = pandas.read_html(xls_file, header=0)[0]\

    # on vire les pre inscrits
    chefs = chefs[chefs['Inscriptions.Type']  < 2]
    len(chefs) \

    return chefs

def extraire_groupes(s, viewstate):
    r = s.get(EFFECTIF_URL, verify=True )\

    soup = BeautifulSoup(r.text)
    viewstate = soup.select("#__VIEWSTATE")[0]['value']
    eventvalidation = soup.select("#__EVENTVALIDATION")[0]['value']\

    formdata = {
        '__VIEWSTATE': viewstate,
        '__VIEWSTATEGENERATOR': 'C9A39B21',
        '__VIEWSTATEENCRYPTED': '',
        '__EVENTVALIDATION': eventvalidation,
        'ctl00$ctl00$_ddDelegations': 0,
        'ctl00$ctl00$MainContent$EntreeContent$_entree$_pilotageEntree$_btnPopupStructure$_tbResult': '406950000 - TERRITOIRE LYON LEVANT',
        'ctl00$ctl00$MainContent$EntreeContent$_entree$_pilotageEntree$_cbStructuresDetaillees': "on",
        'ctl00$ctl00$MainContent$EntreeContent$_entree$_pilotageEntree$_ddSaison': 2015,
        'ctl00$ctl00$MainContent$EntreeContent$_entree$_pilotageEntree$_ddHemisphere': 0,
        'ctl00$ctl00$MainContent$EntreeContent$_entree$_ddTrancheAge': -1,
        "ctl00$ctl00$MainContent$_btnValider.x": 43,
        "ctl00$ctl00$MainContent$_btnValider.y": 13,
        "eo_version": "11.0.20.2",
        "eo_style_keys": "/wFk",
    }\

    r = s.post(EFFECTIF_URL, data=formdata, headers=HEADERS)
    soup = BeautifulSoup(r.text)
    table = soup.select("#ctl00_ctl00_MainContent_DivsContent__table__gvResult")[0].encode("utf-8")
    groupes = pandas.read_html(table, skiprows=range(2))
    \
    return groupes[0]

FORMDATA = {
    '__EVENTTARGET': '',
    '__EVENTARGUMENT': '',
    '__VIEWSTATEGENERATOR': 'F4403698',
    "ctl00$MainContent$_selecteur$_tbCode": "",
    "ctl00$MainContent$_tbCodesFonctions": "",
    "ctl00$MainContent$_ddCategorieMembre":-1,
    "ctl00$MainContent$_ddTypeInscription":-1,
    "ctl00$MainContent$_ddSpecialite":-1,
    "ctl00$MainContent$_ddTypeContact":-1,
    "ctl00$MainContent$_ddDiplome":-1,
    "ctl00$MainContent$_ddQualification": -1,
    "ctl00$MainContent$_ddFormation":-1,
    "ctl00$MainContent$_ddRevue":-1,
    "ctl00$MainContent$_ddMailInfoMouv":-1,
    "ctl00$MainContent$_ddMailInfoExt":-1,
    "ctl00$MainContent$_btnExporter.x":50,
    "ctl00$MainContent$_btnExporter.y":7,
}

#
codes_qualifs = {
    "dir": 1,
    "anim": 2,
    "RU": 3,
}\

def extraire_qualifs(s, viewstate, codes_chefs, qualif):
    formdata = dict(FORMDATA, **{"ctl00$MainContent$_ddQualification": codes_qualifs[qualif],
                                 "ctl00$MainContent$_tbCodesFonctions": codes_chefs,
                                 '__VIEWSTATE': viewstate, })
    r = s.post(EXTRACT_URL, data=formdata, headers=HEADERS)
    xls_file = StringIO.StringIO(r.text.encode("utf-8"))
    qualifs = pandas.read_html(xls_file, header=0)[0]
    qualifs.rename(columns={'QualificationsQualificationJeunesseSports.Libelle':'QualificationsQualificationJeunesseSports.Libelle_%s' % qualif}, inplace=True)
    return qualifs

codes_diplomes = {
    "bafa": 73,
}\

def extraire_diplomes(s, viewstate, codes_chefs, diplome):
    formdata = dict(FORMDATA, **{"ctl00$MainContent$_ddDiplome": codes_diplomes[diplome],
                                 "ctl00$MainContent$_tbCodesFonctions": codes_chefs,
                                 '__VIEWSTATE': viewstate, })
    r = s.post(EXTRACT_URL, data=formdata, headers=HEADERS)
    xls_file = StringIO.StringIO(r.text.encode("utf-8"))
    diplomes = pandas.read_html(xls_file, header=0)[0]
    diplomes.rename(columns={'DiplomesType.Libelle':'DiplomesType.Libelle_%s' % diplome}, inplace=True)
    return diplomes

codes_formations = {
    "tech": 52,
    "appro": 53,
    "approA": 244,
    "apf": 248,
}\

def extraire_formations(s, viewstate, codes_chefs, formation):
    formdata = dict(FORMDATA, **{"ctl00$MainContent$_ddFormation": codes_formations[formation],
                                 "ctl00$MainContent$_tbCodesFonctions": codes_chefs,
                                 '__VIEWSTATE': viewstate, })
    r = s.post(EXTRACT_URL, data=formdata, headers=HEADERS)
    xls_file = StringIO.StringIO(r.text.encode("utf-8"))
    formations = pandas.read_html(xls_file, header=0)[0]
    formations.rename(columns={'FormationsType.Libelle':'FormationsType.Libelle_%s' % formation}, inplace=True)
    return formations

def get_adherent(s, num_adherent):
    ADHERENT_URL = "https://intranet.sgdf.fr/Specialisation/Sgdf/adherents/RechercherAdherent.aspx?code="
    r = s.get("%s%d" % (ADHERENT_URL, num_adherent))
    soup = BeautifulSoup(r.text)
    res = []
    # parse and retrieve two vital form values
    t = soup.select("#ctl00_ctl00_MainContent_DivsContent__ActionsFormation__gvListe")[0]
    for row in t.findAll("tr"):
        cells = row.findAll("td")
        if(len(cells) > 2):
           res += [ (cells[0].text, cells[2].text) ] if cells[1].text == u'Accept\xe9e' else []
    return res

def fusion(**kwargs):
    PACKS = pandas.DataFrame([
        (406953511, "2"),
        (406950710, "2"),
        (406951811, "1"),
        (406950911, "3"),
        (406951011, "2"),
        (406951511, "3"),
        (406950711, "2"),
        (406952211, "2"),
        (406950611, "1"),
        (406951310, "3"),
        (406950613, "1"),
        (406951211, "2"),
        (406952311, "3"),
        (406952411, "1"),
        (406951911, "1"),
        (406952111, "1"),
        (406951510, "3"),
        (406951411, "3"),
        (406951711, "2"),
        (406950811, "1"),
        (406951311, "3"),
        \
        (406953521, "2"),
        (406950720, "2"),
        (406951821, "1"),
        (406950921, "3"),
        (406951021, "2"),
        (406951521, "3"),
        (406950721, "2"),
        (406952221, "2"),
        (406950621, "1"),
        (406951320, "3"),
        (406950622, "1"),
        (406951221, "2"),
        (406952321, "3"),
        (406952421, "1"),
        (406951921, "1"),
        (406952121, "1"),
        (406951520, "3"),
        (406951421, "3"),
        (406951721, "2"),
        (406950821, "1"),
        (406951321, "3"),
        \
        (406953531, "2"),
        (406950730, "2"),
        (406951831, "1"),
        (406950931, "3"),
        (406951031, "2"),
        (406951531, "3"),
        (406950731, "2"),
        (406952231, "2"),
        (406950631, "1"),
        (406951330, "3"),
        (406950632, "1"),
        (406951231, "2"),
        (406952331, "3"),
        (406952431, "1"),
        (406951931, "1"),
        (406952131, "1"),
        (406951530, "3"),
        (406951431, "3"),
        (406951731, "2"),
        (406950831, "1"),
        (406951331, "3"),
        \
        (406953541, "2"),
        (406950740, "2"),
        (406951841, "1"),
        (406950941, "3"),
        (406951041, "2"),
        (406951541, "3"),
        (406950741, "2"),
        (406952241, "2"),
        (406950641, "1"),
        (406951340, "3"),
        (406950643, "1"),
        (406951241, "2"),
        (406952341, "3"),
        (406952441, "1"),
        (406951941, "1"),
        (406952141, "1"),
        (406951540, "3"),
        (406951441, "3"),
        (406951741, "2"),
        (406950841, "1"),
        (406951341, "3"),
    ], columns=[u'Structure.CodeStructure', "pack"])\

    data = kwargs.get('chefs')
    qualifications = kwargs.get('qualifications')
    bafas = kwargs.get('bafas')
    formations = kwargs.get('formations')
    inscriptions = kwargs.get('inscriptions', {})\

    for qualif_name in ['anim', 'dir']:
        data = pandas.merge(data,
                            qualifications[qualif_name][[u'Individu.CodeAdherent', u'QualificationsQualificationJeunesseSports.Libelle_%s' % qualif_name,]],
                            on='Individu.CodeAdherent', suffixes=['', ''], how='outer')\

    data = pandas.merge(data,
                        bafas[[u'Individu.CodeAdherent', u'DiplomesType.Libelle_bafa']],
                        on='Individu.CodeAdherent', suffixes=['', ''], how='outer')\

    for formation_name in ['tech', 'appro', 'approA', 'apf']:
        data = pandas.merge(data,
                            formations[formation_name][[u'Individu.CodeAdherent', u'FormationsType.Libelle_%s' % formation_name]],
                            on='Individu.CodeAdherent', suffixes=['', ''], how='outer')\

    data = pandas.merge(data,
                         pandas.DataFrame([(k, v) for k,v in inscriptions.items() if not v == []],
                                         columns=[u'Individu.CodeAdherent', 'inscriptions']),
                        on='Individu.CodeAdherent', suffixes=['', ''], how='outer')\

    data = data.merge(PACKS, on=u'Structure.CodeStructure')\

    data = data.drop_duplicates(subset=[u'Individu.CodeAdherent', u'Individu.Nom', u'Individu.Prenom',])\

    return data

import time

def export_to_html(data):
    column_selection = [u'Individu.CodeAdherent', u'Individu.Nom', u'Individu.Prenom', u'Structure.CodeStructure',
                        u'QualificationsQualificationJeunesseSports.Libelle_anim', #u'Qualifications.EstTitulaire_anim', u'Qualifications.DateFinValidite_anim',
                        u'QualificationsQualificationJeunesseSports.Libelle_dir', #u'Qualifications.EstTitulaire_dir', u'Qualifications.DateFinValidite_dir',
                        u'DiplomesType.Libelle_bafa',
                        u'FormationsType.Libelle_tech',
                        u'FormationsType.Libelle_approA',
                        u'FormationsType.Libelle_appro',
                        u'FormationsType.Libelle_apf',
                        'inscriptions',
                    ]\

    html_string = ""
    html_string += """<html>
    <head><link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.2/css/bootstrap.min.css"></head>
    <body>
        <div class="alert alert-info">donnees du %s</div>
""" % (time.strftime("%d/%m/%Y %H:%M:%S"))\

    def label_formatter(color):
        def mformatter(x):
            return "<button class='btn btn-xs btn-%s'>%s</button>" % (
                color,
                x.tolist()[0]) if isinstance(x.tolist()[0], basestring) else ""
        return mformatter\

    aggreg_dict = {
        u'QualificationsQualificationJeunesseSports.Libelle_anim' : {'qualif': label_formatter("warning")},
        #u'Qualifications.EstTitulaire_anim' : {'tit': lambda x: "<span class='badge'>titulaire</span>" if 'Oui' in x.tolist() else ""},
        u'QualificationsQualificationJeunesseSports.Libelle_dir' : {'qualif': label_formatter("danger")},
        #u'Qualifications.EstTitulaire_dir' : {'tit': lambda x: "<span class='badge'>titulaire</span>" if 'Oui' in x.tolist() else ""},
        u'FormationsType.Libelle_apf'    : {'formation4': label_formatter("success")},
        u'FormationsType.Libelle_tech'   : {'formation1': label_formatter("success")},
        u'FormationsType.Libelle_approA' : {'formation2': label_formatter("success")},
        u'FormationsType.Libelle_appro'  : {'formation3': label_formatter("success")},
        u'DiplomesType.Libelle_bafa'     : {'diplome': label_formatter("warning")},
        #'inscriptions'                   : {'formation3': lambda x: "%s" % x.tolist()},
        'inscriptions'                   : {'formation3': lambda x: "</br>".join(
            ["<button class='btn btn-xs btn-info' data-toggle='tooltip' data-placement='right' title='inscrit le %s'>%s</button>" % (
                str(f[0][1]), str(f[0][0].encode('utf-8'))) for f in
             [i for i in x.tolist() if isinstance(i, list)]
         ])},
    }\

    pandas.set_option('display.max_colwidth', 999)
    grouped = data.groupby('Structure.Nom')
    for name, group in grouped:
        html_string += "<h1>" + name + "</h1>"
        html_string += group[column_selection].groupby([u'Individu.CodeAdherent', u'Individu.Nom', u'Individu.Prenom']).agg(
            aggreg_dict
        )[aggreg_dict.keys()].to_html(header=False, na_rep="", classes="", escape=False) \

    html_string += """</body>
    </html>"""\

    return html_string

def export_viz(data, groupes):
    html_string = ""
    html_string += """<html>
    <head><link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.2/css/bootstrap.min.css"></head>
    <body>
        <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.2/jquery.min.js"></script>
        <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.2/js/bootstrap.min.js"></script>
        <div class="alert alert-info">donnees du %s</div>
""" % (time.strftime("%d/%m/%Y %H:%M:%S"))\

    html_string += "<div class='container-fluid'>"
    data = data.sort('Structure.CodeStructure')
    for nom, group in data.groupby(['pack', 'Structure.CodeStructure', 'Structure.Nom']):
        qualifications_field = ["QualificationsQualificationJeunesseSports.Libelle_anim", "QualificationsQualificationJeunesseSports.Libelle_dir"]
        (anim_count, dir_count) = group[qualifications_field].count()
        chefs_count = group[u'Individu.CodeAdherent'].count()
        prets = "<span class='badge progress-bar-success'><span class='glyphicon glyphicon-ok'></span></span>" if ((dir_count > 0) and (float(anim_count)/float(chefs_count) >= 0.5)) else "<span class='badge progress-bar-danger'><span class='glyphicon glyphicon-ban-circle'></span></span>"\

        structureID = group.iloc[0]['Structure.CodeStructure']
        effectifs = groupes[groupes[0].str.contains(str(int(structureID)))][range(4,7)].values.tolist()[0]
        \
        html_string += """
    <ul class='list-group'>
        <li class='list-group-item'><b class='list-group-heading'>PACK %s</b> %s <span class='badge'>G %s - F %s - &sum; %s</span></li>
""" % (" - ".join([nom[0], nom[2]]), prets, effectifs[0], effectifs[1], effectifs[2])
        for index, chef in group.sort(["Fonction.Code"]).iterrows():
            if pandas.isnull(chef["Individu.CodeAdherent"]):
                continue
            qualifications_html = "<p>"
            for qualifications_field in ["QualificationsQualificationJeunesseSports.Libelle_anim", "QualificationsQualificationJeunesseSports.Libelle_dir"]:
                color = "warning" if qualifications_field == "QualificationsQualificationJeunesseSports.Libelle_anim" else "danger"
                qualifications_html += "" if pandas.isnull(chef[qualifications_field]) else "<big><span class='label label-%s' style='display: inline-block'>%s</span></big> " % (color, " ".join(chef[qualifications_field].split(' ')[0:2]))
            qualifications_html += "</p>"\

            formations_html = ""
            for formation_field in ["FormationsType.Libelle_apf", "FormationsType.Libelle_tech", "FormationsType.Libelle_appro", "FormationsType.Libelle_approA", "DiplomesType.Libelle_bafa"]:
                color = "success" if formation_field == "DiplomesType.Libelle_bafa" else "success"
                formations_html += "" if pandas.isnull(chef[formation_field]) else "<div class='progress-bar progress-bar-%s' style='width: 35%%'>%s</div>" % (color, chef[formation_field].split(' ')[0])\

            inscriptions_html = "Aucune"
            if isinstance(chef["inscriptions"], list):
                inscriptions_html = pandas.DataFrame(chef["inscriptions"], columns=['nom', 'date']).to_html(header=False, na_rep="", classes="table table-condensed", escape=False)\

            badges_html = """    <div class='row'>
                            <div class='col-xs-4 col-md-4'>
                                <label><span class='more-%d collapse'>Qualifications</span></label>
                                %s
                            </div>
                            <div class='col-xs-8 col-md-8'>
                                <label><span class='more-%d collapse'>Formations</span></label>
                                <div class="progress progress-striped active" style='margin-bottom: 2px;'>%s</div>
                            </div>
                        </div>
                        <div class='row'>
                            <div class='col-xs-4 col-md-4'>
                            </div>
                            <div class='col-xs-8 col-md-8 more-%d collapse'>
                                <label style='display: block'>Inscriptions</label>
                                %s
                            </div>
                        </div>
    """     % (
                int(chef["Individu.CodeAdherent"]), qualifications_html, int(chef["Individu.CodeAdherent"]),
                formations_html, int(chef["Individu.CodeAdherent"]), inscriptions_html)\

            html_string += """
        <li class='list-group-item chef' style="padding-top: 0px; padding-bottom: 0px;" id="%d">
            <div class=''>
                <div class='row'>
                    <div class='col-xs-3 col-md-3'>
                        <h5><a data-toggle="collapse" data-target=".more-%d">%s %s</a></h5>
                    </div>
                    <div class='col-xs-9 col-md-9'>
                    %s
                    </div>
                </div>
            </div>
        </li>
    """     % (
                int(chef["Individu.CodeAdherent"]), int(chef["Individu.CodeAdherent"]),
                chef["Individu.Nom"], chef["Individu.Prenom"],
                badges_html
            )
        html_string += "</ul>"\

    html_string += "</div>"
    html_string += """</body>
    </html>"""\

    return html_string
