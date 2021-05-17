from my_framework.templator import render
from patterns.my_creation_patterns import Engine, Logger, MapperRegistry
from patterns.my_structural_patterns import MyDecorator, DecTimeit
from patterns.my_beh_patterns import EmailNotif, SmsNotif, ListView, CreateView, BaseSerializer
from patterns.my_arch_patterns import UnitOfWork

site = Engine()
logger = Logger('main')
email_notifier = EmailNotif()
sms_notifier = SmsNotif()
UnitOfWork.new_current()
UnitOfWork.get_current().set_mapper_registry(MapperRegistry)

routes = {}


# контроллер - главная страница
@MyDecorator(routes=routes, url='/')
class Index:
    @DecTimeit(name='Index')
    def __call__(self, request):
        return '200 OK', render('index.html', objects_list=site.categories, date=request.get('date', None),
                                python_ver=request.get('python_ver', None))


@MyDecorator(routes=routes, url='/about/')
class About:
    @DecTimeit(name='About')
    def __call__(self, request):
        return '200 OK', render('about.html', date=request.get('date', None))


@MyDecorator(routes=routes, url='/gallery/')
class Gallery:
    @DecTimeit(name='Gallery')
    def __call__(self, request):
        return '200 OK', 'Gallery'


@MyDecorator(routes=routes, url='/hello/')
class Hello:
    @DecTimeit(name='Hello')
    def __call__(self, request):
        return '200 OK', render('hello.html', username=request.get('request_params', {}).get('username'))


class NotFound404:
    @DecTimeit(name='NotFound404')
    def __call__(self, request):
        return '404 WHAT', '404 PAGE Not Found'


# контроллер - список курсов
@MyDecorator(routes=routes, url='/courses-list/')
class CoursesList:
    @DecTimeit(name='CoursesList')
    def __call__(self, request):
        logger.log('Список курсов')
        try:
            category = site.find_category_by_id(int(request['request_params']['id']))
            return '200 OK', render('courses_list.html', objects_list=category.courses, name=category.name,
                                    id=category.id)
        except KeyError:
            return '200 OK', 'No courses have been added yet'


# контроллер - создать курс
@MyDecorator(routes=routes, url='/create-course/')
class CreateCourse:
    category_id = -1

    @DecTimeit(name='CreateCourse')
    def __call__(self, request):
        if request['method'] == 'POST':
            # метод пост
            data = request['data']

            name = data['name']
            name = site.decode_value(name)

            category = None
            if self.category_id != -1:
                category = site.find_category_by_id(int(self.category_id))

                course = site.create_course('record', name, category)
                # Добавляем наблюдателей на курс
                course.observers.append(email_notifier)
                course.observers.append(sms_notifier)
                site.courses.append(course)

            return '200 OK', render('courses_list.html', objects_list=category.courses,
                                    name=category.name, id=category.id)

        else:
            try:
                self.category_id = int(request['request_params']['id'])
                category = site.find_category_by_id(int(self.category_id))

                return '200 OK', render('create_course.html', name=category.name, id=category.id)
            except KeyError:
                return '200 OK', 'No categories have been added yet'


# контроллер - копировать курс
@MyDecorator(routes=routes, url='/clone-course/')
class CloneCourse:
    @DecTimeit(name='CloneCourse')
    def __call__(self, request):
        request_params = request['request_params']

        try:
            name = request_params['name']
            old_course = site.get_course(name)
            if old_course:
                new_name = f'clone_{name}'
                new_course = old_course.clone()
                new_course.name = new_name
                site.courses.append(new_course)

            return '200 OK', render('courses_list.html', objects_list=site.courses)
        except KeyError:
            return '200 OK', 'No courses have been added yet'


# контроллер - создать категорию
@MyDecorator(routes=routes, url='/create-category/')
class CreateCategory:
    @DecTimeit(name='CreateCategory')
    def __call__(self, request):

        if request['method'] == 'POST':
            # метод пост
            print(request)
            data = request['data']

            name = data['name']
            name = site.decode_value(name)

            category_id = data.get('category_id')

            category = None
            if category_id:
                category = site.find_category_by_id(int(category_id))

            new_category = site.create_category(name, category)

            site.categories.append(new_category)

            return '200 OK', render('index.html', objects_list=site.categories)
        else:
            categories = site.categories
            return '200 OK', render('create_category.html', categories=categories)


# контроллер - список категорий
@MyDecorator(routes=routes, url='/category-list/')
class CategoryList:
    @DecTimeit(name='CategoryList')
    def __call__(self, request):
        logger.log('Список категорий')
        return '200 OK', render('category_list.html', objects_list=site.categories)


@MyDecorator(routes=routes, url='/follower-list/')
class FollowerListView(ListView):
    queryset = site.followers
    template_name = 'follower_list.html'

    def get_queryset(self):
        mapper = MapperRegistry.get_current_mapper('follower')
        result = mapper.all()
        for follower in result:
            for course in site.courses:
                for course_follower in course.followers:
                    if course_follower.id == follower.id:
                        follower.courses.append(course)
        return result


@MyDecorator(routes=routes, url='/create-follower/')
class FollowerCreateView(CreateView):
    template_name = 'create_follower.html'

    def create_obj(self, data: dict):
        name = data['name']
        name = site.decode_value(name)
        new_obj = site.create_user('follower', name)
        site.followers.append(new_obj)
        new_obj.mark_new()
        UnitOfWork.get_current().commit()


@MyDecorator(routes=routes, url='/add-follower/')
class AddFollowerByCourseCreateView(CreateView):
    template_name = 'add_follower.html'

    def get_context_data(self):
        context = super().get_context_data()
        context['courses'] = site.courses
        context['followers'] = site.followers
        return context

    def create_obj(self, data: dict):
        course_name = data['course_name']
        course_name = site.decode_value(course_name)
        course = site.get_course(course_name)
        follower_name = data['follower_name']
        follower_name = site.decode_value(follower_name)
        follower = site.get_follower(follower_name)
        course.add_follower(follower)


@MyDecorator(routes=routes, url='/api/')
class CourseApi:
    @DecTimeit(name='CourseApi')
    def __call__(self, request):
        return '200 OK', BaseSerializer(site.courses).save()
