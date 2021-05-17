import copy
from quopri import decodestring
from sqlite3 import connect
import threading
from patterns.my_beh_patterns import ConsoleWriter, Subject
from patterns.my_arch_patterns import DomainObject
#from architectural_system_pattern_mappers import StudentMapper


# creation patterns
# абстрактный пользователь
class User:
    def __init__(self, name):
        self.name = name


# преподаватель - это пользователь
class Guru(User):
    pass


# студент - это пользователь
class Follower(User, DomainObject):
    def __init__(self, name):
        self.courses = []
        super().__init__(name)


# порождающий паттерн Абстрактная фабрика - фабрика пользователей
class UserFactory:
    types = {
        'follower': Follower,
        'guru': Guru
    }

    # порождающий паттерн Фабричный метод
    @classmethod
    def create(cls, type_, name):
        return cls.types[type_](name)


# порождающий паттерн Прототип - Курс
class CoursePrototype:
    # прототип курсов обучения
    def clone(self):
        return copy.deepcopy(self)


class Course(CoursePrototype, Subject):
    def __init__(self, name, category):
        self.name = name
        self.category = category
        self.category.courses.append(self)
        self.followers = []
        super().__init__()

    def __getitem__(self, item):
        return self.followers[item]

    def add_follower(self, follower: Follower):
        self.followers.append(follower)
        follower.courses.append(self)
        self.send_notify()


# Интерактивный курс
class InteractiveCourse(Course):
    pass


# Курс в записи
class RecordCourse(Course):
    pass


# Категория
class Category:
    # начальный id
    auto_id = 0

    def __init__(self, name, category):
        self.id = Category.auto_id
        Category.auto_id += 1
        self.name = name
        self.category = category
        self.courses = []

    def course_count(self):
        result = len(self.courses)
        if self.category:
            result += self.category.course_count()
        return result


# порождающий паттерн Абстрактная фабрика - фабрика курсов
class CourseFactory:
    types = {
        'interactive': InteractiveCourse,
        'record': RecordCourse
    }

    # порождающий паттерн Фабричный метод
    @classmethod
    def create(cls, type_, name, category):
        return cls.types[type_](name, category)


# Основной интерфейс проекта
class Engine:
    def __init__(self):
        self.guru = []
        self.followers = []
        self.courses = []
        self.categories = []

    @staticmethod
    def create_user(type_, name):
        return UserFactory.create(type_, name)

    @staticmethod
    def create_category(name, category=None):
        return Category(name, category)

    def find_category_by_id(self, id):
        for item in self.categories:
            print('item', item.id)
            if item.id == id:
                return item
        raise Exception(f'Нет категории с id = {id}')

    @staticmethod
    def create_course(type_, name, category):
        return CourseFactory.create(type_, name, category)

    def get_course(self, name) -> Course:
        for item in self.courses:
            if item.name == name:
                return item
        return None

    def get_follower(self, name) -> Follower:
        mapper = MapperRegistry.get_current_mapper('follower')
        return mapper.find_by_name(name)

    @staticmethod
    def decode_value(val):
        val_b = bytes(val.replace('%', '=').replace("+", " "), 'UTF-8')
        val_decode_str = decodestring(val_b)
        return val_decode_str.decode('UTF-8')


# порождающий паттерн Синглтон, создаем метакласс
class SingletonMeta(type):
    def __init__(cls, name, bases, attrs, **kwargs):
        super().__init__(name, bases, attrs)
        cls.__instance = {}

    def __call__(cls, *args, **kwargs):
        if args:
            name = args[0]
        if kwargs:
            name = kwargs['name']
        if name in cls.__instance:
            return cls.__instance[name]
        else:
            cls.__instance[name] = super().__call__(*args, **kwargs)
            return cls.__instance[name]


class Logger(metaclass=SingletonMeta):
    writer = ConsoleWriter()

    def __init__(self, name):
        self.name = name

    def log(self, text):
        self.writer.write('SingletonLog --->' + text)


class FollowerMapper:

    def __init__(self, connection):
        self.connection = connection
        self.cursor = connection.cursor()
        self.tablename = 'follower'

    def all(self):
        statement = f'SELECT * from {self.tablename}'
        self.cursor.execute(statement)
        result = []
        for item in self.cursor.fetchall():
            id, name = item
            follower = Follower(name)
            follower.id = id
            result.append(follower)
        return result

    def find_by_id(self, id):
        statement = f"SELECT id, name FROM {self.tablename} WHERE id=?"
        self.cursor.execute(statement, (id,))
        result = self.cursor.fetchone()
        if result:
            return Follower(*result)
        else:
            raise RecordNotFoundException(f'record with id={id} not found')

    def find_by_name(self, name):
        statement = f"SELECT id, name FROM {self.tablename} WHERE name=?"
        self.cursor.execute(statement, (name,))
        result = self.cursor.fetchone()
        if result:
            follower = Follower(result[1])
            follower.id = result[0]
            return follower
        else:
            raise RecordNotFoundException(f'record with name={name} not found')

    def insert(self, obj):
        statement = f"INSERT INTO {self.tablename} (name) VALUES (?)"
        self.cursor.execute(statement, (obj.name,))
        try:
            self.connection.commit()
        except Exception as e:
            raise DbCommitException(e.args)

    def update(self, obj):
        statement = f"UPDATE {self.tablename} SET name=? WHERE id=?"
        # Где взять obj.id? Добавить в DomainModel? Или добавить когда берем объект из базы
        self.cursor.execute(statement, (obj.name, obj.id))
        try:
            self.connection.commit()
        except Exception as e:
            raise DbUpdateException(e.args)

    def delete(self, obj):
        statement = f"DELETE FROM {self.tablename} WHERE id=?"
        self.cursor.execute(statement, (obj.id,))
        try:
            self.connection.commit()
        except Exception as e:
            raise DbDeleteException(e.args)


connection = connect('patterns.sqlite')


# архитектурный системный паттерн - Data Mapper
class MapperRegistry:
    mappers = {
        'follower': FollowerMapper,
    }

    @staticmethod
    def get_mapper(obj):
        print(f"ой ой{obj.__class__}")
        if isinstance(obj, Follower):
            return FollowerMapper(connection)

    @staticmethod
    def get_current_mapper(name):
        return MapperRegistry.mappers[name](connection)


class DbCommitException(Exception):
    def __init__(self, message):
        super().__init__(f'Db commit error: {message}')


class DbUpdateException(Exception):
    def __init__(self, message):
        super().__init__(f'Db update error: {message}')


class DbDeleteException(Exception):
    def __init__(self, message):
        super().__init__(f'Db delete error: {message}')


class RecordNotFoundException(Exception):
    def __init__(self, message):
        super().__init__(f'Record not found: {message}')
