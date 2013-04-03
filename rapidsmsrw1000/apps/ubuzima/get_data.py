from rapidsmsrw1000.apps.ubuzima.models import ReportType, Field
from rapidsmsrw1000.apps.chws.models import District


def get_report_counts(report_type, start=None, end=None, date_field='date'):
    """
    Returns a list of dictionaries, one for each district. Each dictionary
    contains:
        district - the name of the district
        province - the name of the district's province
        count - the total number of reports of the specified report type and period.
    """
    if isinstance(report_type, basestring):
        report_type = ReportType.objects.get(name__iexact=report_type)

    filters = {'type': report_type}
    filters.update(_get_date_filters(start, end, date_field))

    data = []
    for district in District.objects.all():
        province_name = _clean_province_name(district.province.name)
        if province_name:
            data.append({
                'district': district.name,
                'province': province_name,
                'count': district.reportdistrict.filter(**filters).count(),
            })
    return data


def get_red_alert_data(start=None, end=None, date_field='date'):
    """
    Returns a list of dictionaries, one for each district. Each dictionary
    contains:
        district - the name of the district
        province - the name of the district's province
        total_count - the total number of Red Alert reports during the period
        counts - a dictionary relating risk field_types and the number of times
            each was reported.
    """
    filters = {'type': ReportType.objects.get(name__iexact='red alert')}
    filters.update(_get_date_filters(start, end, date_field))

    risk_field_types = Field.get_risk_fieldtypes()
    data = []
    for district in District.objects.all():
        province_name = _clean_province_name(district.province.name)
        if province_name:
            risk_reports = district.reportdistrict.filter(**filters)
            for risk in risk_field_types:
                for report in risk_reports:
                    data.append({
                        'district': district.name,
                        'province': province_name,
                        'type': risk.description,
                        'total': report.fields.filter(type=risk).count()
                    })
    return data


def _clean_province_name(name):
    """Evan's compulsions about what the province name should look like."""
    return {
        'KIGALI CITY': 'KIGALI CITY',
        'SOUTHEN PROVINCE': 'SOUTHERN',
        'WESTERN PROVINCE': 'WESTERN',
        'NORTHERN PROVINCE': 'NORTHERN',
        'EASTERN PROVINCE': 'EASTERN',
    }.get(name, None)


def _get_date_filters(start, end, date_field):
    filters = {}
    if date_field:
        if start:
            filters[date_field + '__gte'] = start
        if end:
            filters[date_field + '__lt'] = end
    elif start or end:
        raise Exception('Must specify a date field')
    return filters
