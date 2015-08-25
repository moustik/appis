# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class Member(scrapy.Item):
    def get_collection_name(self): return "members"

    _id = scrapy.Field()
    nom = scrapy.Field()
    prenom = scrapy.Field()
    nom_de_jeune_fille = scrapy.Field()
    adresse = scrapy.Field()
    code_postal = scrapy.Field()
    ville = scrapy.Field()
    pays = scrapy.Field()
    npai = scrapy.Field()
    telephone_domicile = scrapy.Field()
    telephone_professionnel = scrapy.Field()
    telephones_portables = scrapy.Field()
    courriels = scrapy.Field()
    date_de_naissance = scrapy.Field()
    lieu_de_naissance = scrapy.Field()
    profession = scrapy.Field()
    numero_allocataire = scrapy.Field()
    structure = scrapy.Field()
    fonction = scrapy.Field()

class Structure(scrapy.Item):
    def get_collection_name(self): return "structures"

    _id = scrapy.Field()
    name = scrapy.Field()
    parent = scrapy.Field()
    headcount = scrapy.Field()


class Inscription(scrapy.Item):
    def get_collection_name(self): return "inscriptions"

    member_id = scrapy.Field()
    ends = scrapy.Field()
    inscription_type = scrapy.Field()


class Formation(scrapy.Item):
    """
    db.formations.ensureIndex({member_id: 1, name: 1, date: 1}, {unique:true})

    """
    def get_collection_name(self): return "formations"

    member_id = scrapy.Field()
    name = scrapy.Field()
    role = scrapy.Field()
    date = scrapy.Field()
    place = scrapy.Field()


class Diplome(scrapy.Item):
    """
    db.diplomes.ensureIndex({member_id: 1, name: 1, date: 1}, {unique:true})

    """
    def get_collection_name(self): return "diplomes"

    member_id = scrapy.Field()
    name = scrapy.Field()
    date = scrapy.Field()


class Qualification(scrapy.Item):
    """
    db.qualifications.ensureIndex({member_id: 1, name: 1, obtained: 1}, {unique:true})

    """

    def get_collection_name(self): return "qualifications"

    member_id = scrapy.Field()
    name = scrapy.Field()
    titular = scrapy.Field()
    obtained = scrapy.Field()
    expires = scrapy.Field()


class Fonction(scrapy.Item):
    def get_collection_name(self): return "fonctions"

    _id = scrapy.Field()
    name = scrapy.Field()
    category = scrapy.Field()
