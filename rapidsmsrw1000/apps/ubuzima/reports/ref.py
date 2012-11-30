####SAMPLE MESSAGE #####
##res_EN = "The correct format message is: CHI MOTHER_ID CHILD_NUM DOB VACCINS VACCIN_SERIE ACTION_CODE LOCATION_CODE CHILD_WEIGHT MUAC"
##res_FR = "Andika: CHI INDANGAMUNTU IMPANGA NUMERO ITARIKI_AVUTSE IGITSINA IBIBAZO AHO_AVUKIYE KONKA IBIRO"
##msg = "REF 0787321456060612 01 13.02.2011 V2 VI PM NP HP WT72.3 MUAC5.4"
###m = re.search("chi\s+(\d+)\s+([0-9]+)\s([0-9.]+)\s(v1|v2|v3|v4|v5|v6)\s(vc|vi)\s?(.*)\s(ho|hp|cl|or)\s(wt\d+\.?\d)\s(muac\d+\.?\d)\s?(.*)", msg, re.IGNORECASE)
##m = re.search("chi\s+(\d+)\s+([0-9]+)\s([0-9.]+)\s?(.*|v1|v2|v3|v4|v5|v6)\s?(.*|vc|vi)\s?(.*)\s(ho|hp|cl|or)\s(wt\d+\.?\d)\s(muac\d+\.?\d)\s?(.*)", msg, re.IGNORECASE)##for v ignored 
###groups = ('1198156435491265', 'TW', '01', '13.02.2011', 'GI', 'PM NP', 'HP', 'BF1', 'WT72.3', '')
#        nid = m.group(1)
#        number = m.group(2)
#        dob = m.group(3)
#        vaccins = m.group(4)
#        vaccin_serie = m.group(5)
#        ibibazo = m.group(6)
#        location = m.group(7)
#        weight = m.group(8)
#        muac = m.group(9)   

    @keyword("\s*ref(.*)")
    def ref(self, message, notice):
        if not getattr(message, 'reporter', None):
            message.respond(_("You need to be registered first, use the REG keyword"))
            return True
    	rez = re.match(r'ref\s+(\d+)', message.text, re.IGNORECASE)
    	if not rez:
    	    message.respond(_('You never reported a refusal. Refusals are \
reported with the keyword REF'))
    	    return True
    	ref = Refusal(reporter = message.reporter, refid = rez.group(1))
    	ref.save()
        message.respond(_('It has been recorded.'))
        return True
