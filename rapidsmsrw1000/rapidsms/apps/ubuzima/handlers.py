import django_tables2 as tables

class PatientTable(tables.Table):
    nid = tables.Column(verbose_name='national id')
    location = tables.Column(verbose_name='health centre')
    district = tables.Column(verbose_name='district')
    province = tables.Column(verbose_name='province')
