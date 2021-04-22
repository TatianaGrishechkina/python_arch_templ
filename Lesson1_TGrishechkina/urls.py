from sys import version_info
from datetime import date
from views import Index, About, Gallery, Hello


# front controller
def secret_front(request):
    request['date'] = date.today()


def other_front(request):
    request['key'] = 'key'


def version_front(request):
    request['python_ver'] = f'{version_info.major}.{version_info.minor}'


fronts = [secret_front, other_front, version_front]

routes = {
    '/': Index(),
    '/about/': About(),
    '/gallery/': Gallery(),
    '/hello/': Hello(),
}
