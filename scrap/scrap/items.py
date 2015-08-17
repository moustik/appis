# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class ScrapItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class Member(scrapy.Item):
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
