import unicodedata

import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.selector import HtmlXPathSelector

from scrap.items import *

INTRANET_URL = "https://intranet.sgdf.fr"
MEMBER_URL = "https://intranet.sgdf.fr/Specialisation/Sgdf/adherents/RechercherAdherent.aspx"
EXTRACT_URL = "https://intranet.sgdf.fr/Specialisation/Sgdf/Adherents/ExtraireAdherents.aspx"
HEADCOUNT_URL = "https://intranet.sgdf.fr/Specialisation/Sgdf/Pilotage/Adherents/EffectifTotalCategorieSexe.aspx"


def clean_field_name(field_name):
    return unicodedata.normalize('NFKD', field_name.strip().lower()).encode('ascii', 'ignore').replace(" ", "_")


def value(selector):
    return selector.xpath('text()')[0].extract() if len(selector.xpath('text()')) else None

class SGDFIntranetSpider(scrapy.Spider):
    name = "intranet"
    start_urls = [INTRANET_URL]


    def parse(self, response):
        self.logger.info("Logging in")
        return scrapy.FormRequest.from_response(
            response,
            formdata={'ctl00$MainContent$login': self.crawler.settings.get('SGDFLOGIN', ""),
                      'ctl00$MainContent$password': self.crawler.settings.get('SGDFPASS', "")},
            callback=self.retrieve_member_form_after_login)


    def retrieve_member_form_after_login(self, response):
        if "Identifiant invalide" in response.body:
            self.logger.error("Could not log in")
        else:
            self.logger.warning("Logged in !")

            for i in [1]:
                yield scrapy.FormRequest(
                    HEADCOUNT_URL,
                    callback=self.push_headcount_form)

            for i in [1]:
                yield scrapy.FormRequest(
                    EXTRACT_URL,
                    callback=self.push_member_form)


    def push_member_form(self, response):
        return scrapy.FormRequest.from_response(
            response,
            formdata={
          "ctl00$MainContent$_selecteur$_tbCode": "",
          "ctl00$MainContent$_tbCodesFonctions": "",
          "ctl00$MainContent$_ddCategorieMembre": '-1',
          "ctl00$MainContent$_ddTypeInscription": '-1',
          "ctl00$MainContent$_ddSpecialite":'-1',
          "ctl00$MainContent$_ddTypeContact":'-1',
          "ctl00$MainContent$_ddDiplome":'-1',
          "ctl00$MainContent$_ddQualification":'-1',
          "ctl00$MainContent$_ddFormation":'-1',
          "ctl00$MainContent$_ddRevue":'-1',
          "ctl00$MainContent$_ddMailInfoMouv":'-1',
          "ctl00$MainContent$_ddMailInfoExt":'-1',
          "ctl00$MainContent$_cbExtraireIndividu": "on",
          "ctl00$MainContent$_cbExtraireInscription": "on",
          "ctl00$MainContent$_btnExporter.x": '50',
          "ctl00$MainContent$_btnExporter.y": '7',
            },
            callback=self.parse_member_list)


    def parse_member_list(self, response):
# tests
#        return scrapy.Request(MEMBER_URL + "?code=152606745",
#                              callback=self.parse_member)
#
#    def blah(self, response):
        hxs = scrapy.selector.HtmlXPathSelector(text=response.body)
#        from scrapy.shell import inspect_response
#        inspect_response(response, self)

#            [
# 0              u'IndividuCivilite.NomCourt', u'Individu.CodeAdherent', u'Individu.Nom', u'Individu.Prenom',
# 4              u'Structure.CodeStructure', u'Structure.Nom',
# 6              u'Fonction.Code', u'Fonction.CategorieMembre', u'Fonction.NomMasculin', u'Fonction.NomFeminin',
# 10                 u'Inscription.Delegations',
# 11             u'Individu.NomJeuneFille', u'Individu.Adresse.Ligne1', u'Individu.Adresse.Ligne2', u'Individu.Adresse.Ligne3',
# 15             u'Individu.Adresse.CodePostal', u'Individu.Adresse.Municipalite', u'Individu.Adresse.Pays',
# 18             u'Individu.TelephoneDomicile', u'Individu.TelephonePortable1', u'Individu.TelephonePortable2',
# 21             u'Individu.TelephoneBureau', u'Individu.Fax',
# 23             u'Individu.CourrielPersonnel', u'Individu.CourrielProfessionnel',
# 25             u'Individu.DateNaissance', u'Individu.LieuNaissance', u'IndividuPaysNaissance.PaysLib',
# 28             u'Individu.Profession', u'Individu.NumeroAllocataire',
# 30             u'Individu.RegimeCAF', u'Individu.RegimeMSA', u'Individu.RegimeMaritime', u'Individu.RegimeAutre',
# 34                 u'Individu.RegimeAllocataire',
# 35             u'Individu.AutorisationInterventionChirurgicale', u'Individu.DroitImage',
# 37                 u'Individu.AssuranceResponsabiliteCivile',
# 38             u'Individu.AutoriseMailInfoMouvement', u'Individu.AutoriseMailInfoExterne',
# 40             u'Inscriptions.DateDebut', u'Inscriptions.DateFin', u'Inscriptions.Type']

        for member_selector in hxs.xpath('/html/body/table/tr')[1:]:
            member_id_hxs = member_selector.xpath('td')[1].xpath('text()')
            if len(member_id_hxs):
                member_id = member_id_hxs[0].extract()
            else:
                self.logger.warning("no member ID")
                continue
            self.logger.warning("extracting %s" % member_id)

            member = Member(id=int(member_id),
                            structure=int(value(member_selector.xpath('td')[4])),
                            fonction=value(member_selector.xpath('td')[6]),
                            inscription_starts=value(member_selector.xpath('td')[40]),
                            inscription_ends=value(member_selector.xpath('td')[41]),
                            inscription_type=int(value(member_selector.xpath('td')[42])),
            )

            for i in [1]:
                yield scrapy.Request(MEMBER_URL + "?code=%s" % member_id,
                                     callback=self.parse_member,
                                     meta={"member": member})

            inscription = Inscription(member_id=int(member_id),
                                      starts=value(member_selector.xpath('td')[40]),
                                      ends=value(member_selector.xpath('td')[41]),
                                      inscription_type=int(value(member_selector.xpath('td')[42])),
            )
            for i in [1]:
                yield inscription

            fonction = Fonction(id=value(member_selector.xpath('td')[6]),
                                name=value(member_selector.xpath('td')[8]),
                                category=int(value(member_selector.xpath('td')[7])),
            )
            for i in [1]:
                yield fonction




    def parse_member(self, response):
#        from scrapy.shell import inspect_response
#        inspect_response(response, self)
        id = value(response.xpath('//*[@id="ctl00_ctl00_MainContent_TabsContent_TabContainerResumeAdherent__tabResume__resume__lblCodeAdherent"]'))
        id = int(id) if id else -1
        try:
            full_name = response.xpath('//*[@id="ctl00_ctl00__divTitre"]/text()')[0].extract().split(' ')
        except:
            self.logger.error(response.request)
            full_name = ["erreur", "erreur", "erreur"]

        if len(full_name):
            full_name = full_name[1:]
        else:
            return


        item = response.meta.get("member")
        item["nom"] = full_name[0]
        item["prenom"] = full_name[1]

        for row_selector in response.xpath('//*[@id="ctl00_ctl00_MainContent_TabsContent_TabContainerResumeAdherent__tabResume"]/table/tr')[1:-1]: # skip header and alloc CAF
            label = row_selector.xpath('td[@class="label_fiche"]/text()')[0].extract()
            field = row_selector.xpath(
                "*//*[starts-with(@id, 'ctl00_ctl00_MainContent_TabsContent_TabContainerResumeAdherent__tabResume__resume__modeleIndividu__')]/text()"
            ).extract()
#            self.logger.warning((clean_field_name(label), field))
            try:
                item[clean_field_name(label)] = field[0] if len(field) else None
            except:
                pass

        for i in [1]:
            yield scrapy.FormRequest.from_response(
                response,
                headers={
                    "Accept": "*/*",
                    "X-MicrosoftAjax": "Delta=true",
                    "X-Requested-With": "XMLHttpRequest",
                },
                formdata={
                    "ctl00$ctl00$ScriptManager1": "ctl00$ctl00$_upMainContent|ctl00$ctl00$MainContent$TabsContent$TabContainerResumeAdherent",
                    "__EVENTTARGET": "ctl00$ctl00$MainContent$TabsContent$TabContainerResumeAdherent",
                    "__EVENTARGUMENT:activeTabChanged": "5",
                    "__ASYNCPOST": "true",
                    "ctl00_ctl00_MainContent_TabsContent_TabContainerResumeAdherent_ClientState": '{"ActiveTabIndex":5,"TabState":[true,true,true,true,true,true,true,true,true,true]}',
                },
                callback=self.parse_member_formation_tab,
                meta= {'id': id})

        for i in [1]:
            yield item



    def parse_member_formation_tab(self, response):
        id = response.meta.get("id")

        for row_selector in response.xpath('//*[@id="ctl00_ctl00_MainContent_TabsContent_TabContainerResumeAdherent__tabFormations__formations__gvFormations__gvFormations"]/tr')[1:]:
            formation = Formation(member_id=id)
            formation["name"] = value(row_selector.xpath('td')[0])
            formation["role"] = value(row_selector.xpath('td')[1])
            formation["date"] = value(row_selector.xpath('td')[2])
            yield formation

        for row_selector in response.xpath('//*[@id="ctl00_ctl00_MainContent_TabsContent_TabContainerResumeAdherent__tabFormations__formations__gvDiplomes__gvDiplomes"]/tr')[1:]:
            diplome = Diplome(member_id=id)
            diplome["name"] = value(row_selector.xpath('td')[0])
            diplome["date"] = value(row_selector.xpath('td')[2])
            yield diplome

        for row_selector in response.xpath('//*[@id="ctl00_ctl00_MainContent_TabsContent_TabContainerResumeAdherent__tabFormations__qualifications__gvQualifications__gvQualifications"]/tr')[1:]:
            qualification = Qualification(member_id=id)
            qualification["name"] = value(row_selector.xpath('td')[0]).strip()
            qualification["titular"] = value(row_selector.xpath('td')[1])
            qualification["obtained"] = value(row_selector.xpath('td')[2])
            qualification["expires"] = value(row_selector.xpath('td')[3])
            yield qualification


# import cgi, pprint
# from pprint import pprint as pp
# pprint.pprint(cgi.parse_qs(request.body).keys())
# response.xpath("//table")
# response.xpath('//*[@id="ctl00_MainContent__recherche__gvResultats"]')


#                'ctl00$MainContent$_recherche$_selecteur$_autocompleteStructures$_txtAutoComplete': '949506',
#                'ctl00$MainContent$_recherche$_selecteur$_tbCode': '949506',
#                'ctl00$MainContent$_recherche$_cbRecursif': 'on',
#                'ctl00$MainContent$_recherche$_ddCategorieMembres': '-1',
#                'ctl00$MainContent$_recherche$_autoCompleteFonctions$_txtAutoComplete': '210',
#                'ctl00$MainContent$_recherche$_autoCompleteFonctions$_hiddenAutoComplete': '',
#                'ctl00$MainContent$_recherche$_tbCode': '',
#                'ctl00$MainContent$_recherche$_tbNom': '',
#                'ctl00$MainContent$_recherche$_tbPrenom': '',
#                'ctl00$MainContent$_recherche$_cpDateNaissance$textBox': '',
#                'ctl00$MainContent$_recherche$_cpDateNaissance$hidden': '',
#                'ctl00$MainContent$_recherche$_cpDateNaissance$validateHidden': '',
#                'ctl00$MainContent$_recherche$_cpDateNaissance$enableHidden': 'true',
#                'ctl00$MainContent$_recherche$_tbCodePostal': '',
#                'ctl00$MainContent$_recherche$_tbVille': '',
#                '__ASYNCPOST': 'true',
#                'ctl00$ScriptManager1': 'ctl00$_upMainContent|ctl00$MainContent$_recherche$_btnRechercher',
#                'ctl00_MainContent__recherche__pnlFormulaire_CurrentState': 'false',
#                'ctl00$MainContent$_recherche$_btnRecherche.x': '57',
#                'ctl00$MainContent$_recherche$_btnRecherche.y': '9',

#           dont_click=True,


    def push_headcount_form(self, response):
        return scrapy.FormRequest.from_response(
            response,
            formdata={
                'ctl00$ctl00$MainContent$EntreeContent$_entree$_pilotageEntree$_btnPopupStructure$_tbResult': '406950000 - TERRITOIRE LYON LEVANT',
                'ctl00$ctl00$MainContent$EntreeContent$_entree$_pilotageEntree$_cbStructuresDetaillees': "on",
                'ctl00$ctl00$MainContent$EntreeContent$_entree$_pilotageEntree$_ddSaison': "2016",
                'ctl00$ctl00$MainContent$EntreeContent$_entree$_pilotageEntree$_ddHemisphere': "0",
                'ctl00$ctl00$MainContent$EntreeContent$_entree$_ddTrancheAge': "-1",
                "ctl00$ctl00$MainContent$_btnValider.x": "43",
                "ctl00$ctl00$MainContent$_btnValider.y": "13",
            },
            callback=self.parse_headcount)


    def parse_headcount(self, response):

        for row_selector in response.xpath('//table[@id="ctl00_ctl00_MainContent_DivsContent__table__gvResult"]/tr')[2:-1]:
            structure = Structure()
            structure["id"] = int(value(row_selector.xpath('td')[0]).split(' - ')[0])
            structure["name"] = value(row_selector.xpath('td')[0]).split(' - ')[1]
            structure["headcount"] = [ int(value(row_selector.xpath('td')[i])) for i in range(1,13) ]
            yield structure

