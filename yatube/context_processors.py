import datetime as dt


def get_this_year(request):
    this_year = dt.datetime.now().year
    return {'this_year': this_year}
