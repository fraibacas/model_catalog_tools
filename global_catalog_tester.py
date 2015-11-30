
import Globals
from Products.ZenUtils.ZenScriptBase import ZenScriptBase
dmd = ZenScriptBase(connect=True).dmd
from transaction import commit


from Products.AdvancedQuery import Eq, Or, Generic, And, In, MatchRegexp
from Products.Zuul.catalog.interfaces import IModelCatalogTool
from Products.Zuul.interfaces.tree import ICatalogTool
from zenoss.modelindex.searcher import SearchParams
from zenoss.modelindex.exceptions import SearchException

import random
import time

from utils import get_device_classes, get_mib_organizers

DEVICE_CLASSES = get_device_classes(dmd)

class GlobalCatalogTester(object):

    def __init__(self):
        pass

    def test_device_classes_devices(self):
        """ Check devices under device classes are the same """
        failed_device_classes = []
        for dc in DEVICE_CLASSES:
            dc_object = dmd.unrestrictedTraverse(dc)

            # Devices under device class in global catalog
            global_catalog = ICatalogTool(dc_object)
            global_catalog_brains = global_catalog.search('Products.ZenModel.Device.Device')
            global_catalog_results = set([ brain.getPath() for brain in global_catalog_brains.results ])

            # Devices under device class in model catalog
            model_catalog = IModelCatalogTool(dc_object)
            model_catalog_brains = model_catalog.search('Products.ZenModel.Device.Device', limit=10000)
            model_catalog_results = set([ brain.getPath() for brain in model_catalog_brains.results ])

            result = "FAILED"
            if len(global_catalog_results - model_catalog_results) == 0 and  \
               len(model_catalog_results-global_catalog_results) ==0:
               result = "PASSED"
            else:
                failed_device_classes.append(dc)

        if not failed_device_classes:
            print "TEST PASSED: All devices found in the same device classes for both catalogs!!"
        else:
            print "TEST FAILED: The following device classes have different devices in the catalogs:"
            for failed in failed_device_classes:
                print "\t{0}".format(failed)

        return len(failed_device_classes) == 0


    def validate_mib_counts(self):
        """ """
        mib_organizers = get_mib_organizers(dmd)
        failed_counts = []
        global_catalog = ICatalogTool(dmd)
        model_catalog = IModelCatalogTool(dmd)
        for organizer in mib_organizers:
            global_catalog_count = global_catalog.count(("Products.ZenModel.MibModule.MibModule",), organizer)
            model_catalog_count = model_catalog.count(("Products.ZenModel.MibModule.MibModule",), organizer)
            if global_catalog_count != model_catalog_count:
                failed_counts.append(organizer)

        if not failed_counts:
            print "TEST PASSED: All mib organizers have the same count in both catalogs!!"
        else:
            print "TEST FAILED: The following mib organizers have different counts in the catalogs:"
            for failed in failed_counts:
                print "\t{0}".format(failed)
        return len(failed_counts) == 0

    def validate_templates(self):
        """ Check that both catalogs return same data for templates """
        global_catalog = ICatalogTool(dmd.Devices)
        model_catalog = IModelCatalogTool(dmd.Devices)

        # get template nodes from global catalog
        global_catalog_brains = global_catalog.search(types=('Products.ZenModel.RRDTemplate.RRDTemplate',))
        global_catalog_templates = set([ brain.getPath() for brain in global_catalog_brains ])

        # get template nodes from model catalog
        model_catalog_brains = global_catalog.search(types=('Products.ZenModel.RRDTemplate.RRDTemplate',))
        model_catalog_templates = set([ brain.getPath() for brain in model_catalog_brains ])

        # compare results
        if len(model_catalog_templates - global_catalog_templates) == 0 and \
            len(global_catalog_templates - model_catalog_templates) == 0:
            for template in global_catalog_templates:
                template_object = dmd.unrestrictedTraverse(template)
                query = Eq('id', template_object.id)
                
                gc_brains = global_catalog.search(types=('Products.ZenModel.RRDTemplate.RRDTemplate',), query=query)
                gc_templates = set([ brain.getPath() for brain in gc_brains ])

                mc_brains = model_catalog.search(types=('Products.ZenModel.RRDTemplate.RRDTemplate',), query=query)
                mc_templates = set([ brain.getPath() for brain in mc_brains ])

                failed_templates = []
                if not (len(mc_templates - gc_templates) == 0 and \
                   len(gc_templates - mc_templates) == 0):
                    failed_templates.append(template)

            if failed_templates:
                print "TEST FAILED: Inconsistent results from catalogs for templates:"
                for failure in failed_templates:
                    print "\t{0}".format(failure)
            else:
                print "TEST PASSED: Both catalogs returned same results!!"
                return True

        else:
            print "TEST FAILED: Inconsistent results from catalogs:"
            print "\t{0}".format("Templates found in global catalog and not in model catalog: {0}".format(global_catalog_templates - model_catalog_templates))
            print "\t{0}".format("Templates found in model catalog and not in global catalog: {0}".format(model_catalog_templates - global_catalog_templates))

        return False

    def run(self):
        return self.test_device_classes_devices() and self.validate_mib_counts() and self.validate_templates()


class ScenationPrepper(object):
    """ Creates some random devices, systems, and location """

    LOCATIONS = [ "Tokyo, Japan", "Jakarta, Indonesia", "Seoul, South Korea", "Delhi, India", \
                  "Shanghai, China", "Manila, Philippines", "Karachi, Pakistan", "New York, USA", \
                  "Sao Paulo, Brazil", "Mexico City, Mexico", "Cairo, Egypt", "Beijing, China", \
                  "Osaka, Japan", "Mumbai (Bombay), India", "Guangzhou, China", "Moscow, Russia", \
                  "Los Angeles, USA", "Calcutta, India", "Dhaka, Bangladesh", "Buenos Aires, Argentina", \
                  "Istanbul, Turkey", "Rio de Janeiro, Brazil", "Shenzhen, China", "Lagos, Nigeria", "Paris, France", \
                  "Nagoya, Japan", "Lima, Peru", "Chicago, USA", "Kinshasa, Congo", "Tianjin, China" ]

    #SYSTEMS = [ "Mercury", "Venus", "Earth", "Mars", "Asteroids", "Jupiter", "Saturn", "Uranus", "Neptune", "ACAMAR", "ACHERNAR", "Achird", "ACRUX", "Acubens", "ADARA", "Adhafera", "Adhil", "AGENA", "Ain al Rami", "Ain", "Al Anz", "Al Kalb al Rai", "Al Minliar al Asad", "Al Minliar al Shuja", "Aladfar", "Alathfar", "Albaldah", "Albali", "ALBIREO", "Alchiba", "ALCOR", "ALCYONE", "ALDEBARAN", "ALDERAMIN", "Aldhibah", "Alfecca Meridiana", "Alfirk", "ALGENIB", "ALGIEBA", "ALGOL", "Algorab", "ALHENA", "ALIOTH", "ALKAID", "Alkalurops", "Alkes", "Alkurhah", "ALMAAK", "ALNAIR", "ALNATH", "ALNILAM", "ALNITAK", "Alniyat", "Alniyat", "ALPHARD", "ALPHEKKA", "ALPHERATZ", "Alrai", "Alrisha", "Alsafi", "Alsciaukat", "ALSHAIN", "Alshat", "Alsuhail", "ALTAIR", "Altarf", "Alterf", "Aludra", "Alula Australis", "Alula Borealis", "Alya", "Alzirr", "Ancha", "Angetenar", "ANKAA", "Anser", "ANTARES", "ARCTURUS", "Arkab Posterior", "Arkab Prior", "ARNEB", "Arrakis", "Ascella", "Asellus Australis", "Asellus Borealis", "Asellus Primus", "Asellus Secondus", "Asellus Tertius", "Asterope", "Atik", "Atlas", "Auva", "Avior", "Azelfafage", "Azha", "Azmidiske", "Baham", "Baten Kaitos", "Becrux", "Beid", "BELLATRIX", "BETELGEUSE", "Botein", "Brachium", "CANOPUS", "CAPELLA", "Caph", "CASTOR", "Cebalrai", "Celaeno", "Chara", "Chort", "COR CAROLI", "Cursa", "Dabih", "Deneb Algedi", "Deneb Dulfim", "Deneb el Okab", "Deneb el Okab", "Deneb Kaitos Shemali", "DENEB", "DENEBOLA", "Dheneb", "Diadem", "DIPHDA", "Dschubba", "Dsiban", "DUBHE", "Ed Asich", "Electra", "ELNATH", "ENIF", "ETAMIN", "FOMALHAUT", "Fornacis", "Fum al Samakah", "Furud", "Gacrux", "Gianfar", "Gienah Cygni", "Gienah Ghurab", "Gomeisa", "Gorgonea Quarta", "Gorgonea Secunda", "Gorgonea Tertia", "Graffias", "Grafias", "Grumium", "HADAR", "Haedi", "HAMAL", "Hassaleh", "Head of Hydrus", "Herschel's "Garnet Star"", "Heze", "Hoedus II", "Homam", "Hyadum I", "Hyadum II", "IZAR", "Jabbah", "Kaffaljidhma", "Kajam", "KAUS AUSTRALIS", "Kaus Borealis", "Kaus Meridionalis", "Keid", "Kitalpha", "KOCAB", "Kornephoros", "Kraz", "Kuma", "Lesath", "Maasym", "Maia", "Marfak", "Marfak", "Marfic", "Marfik", "MARKAB", "Matar", "Mebsuta", "MEGREZ", "Meissa", "Mekbuda", "Menkalinan", "MENKAR", "Menkar", "Menkent", "Menkib", "MERAK", "Merga", "Merope", "Mesarthim", "Metallah", "Miaplacidus", "Minkar", "MINTAKA", "MIRA", "MIRACH", "Miram", "MIRPHAK", "MIZAR", "Mufrid", "Muliphen", "Murzim", "Muscida", "Muscida", "Muscida", "Nair al Saif", "Naos", "Nash", "Nashira", "Nekkar", "NIHAL", "Nodus Secundus", "NUNKI", "Nusakan", "Peacock", "PHAD", "Phaet", "Pherkad Minor", "Pherkad", "Pleione", "Polaris Australis", "POLARIS", "POLLUX", "Porrima", "Praecipua", "Prima Giedi", "PROCYON", "Propus", "Propus", "Propus", "Rana", "Ras Elased Australis", "Ras Elased Borealis", "RASALGETHI", "RASALHAGUE", "Rastaban", "REGULUS", "Rigel Kentaurus", "RIGEL", "Rijl al Awwa", "Rotanev", "Ruchba", "Ruchbah", "Rukbat", "Sabik", "Sadalachbia", "SADALMELIK", "Sadalsuud", "Sadr", "SAIPH", "Salm", "Sargas", "Sarin", "Sceptrum", "SCHEAT", "Secunda Giedi", "Segin", "Seginus", "Sham", "Sharatan", "SHAULA", "SHEDIR", "Sheliak", "SIRIUS", "Situla", "Skat", "SPICA", "Sterope II", "Sualocin", "Subra", "Suhail al Muhlif", "Sulafat", "Syrma", "Talitha", "Tania Australis", "Tania Borealis", "TARAZED", "Taygeta", "Tegmen", "Tejat Posterior", "Terebellum", "Terebellum", "Terebellum", "Terebellum", "Thabit", "Theemim", "THUBAN", "Torcularis Septentrionalis", "Turais", "Tyl", "UNUKALHAI", "VEGA", "VINDEMIATRIX", "Wasat", "Wezen", "Wezn", "Yed Posterior", "Yed Prior", "Yildun", "Zaniah", "Zaurak", "Zavijah", "Zibal", "Zosma", "Zuben Elakrab", "Zuben Elakribi", "Zuben Elgenubi", "Zuben Elschemali" ]

    def __init__(self):
        pass



def main():
    success = GlobalCatalogTester().run()
    print "\n============================="
    if success:
        print "  TEST PASSED"
    else:
        print "  TEST FAILED"
    print "============================="


if __name__ == '__main__':
    main()
