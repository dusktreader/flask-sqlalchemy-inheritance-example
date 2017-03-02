from buzz import Buzz

db = CemAlchemy(query_class=CemQuery)
app = flask.Flask(
    __name__,
    static_folder='../docs/build/_static',
    template_folder='../docs/templates/',
)

class classproperty(property):  # noqa
    def __get__(self, cls, owner):
        return classmethod(self.fget).__get__(None, owner)()


class ExampleBase(db.Model):

    __abstract__ = True

    def __repr__(self):
        """
        Produces a basic string representation of the model without
        property details
        """
        pk_names = [k.name for k in inspect(self.__class__).primary_key]
        pk_values = [str(getattr(self, n)) for n in pk_names]
        pk_string = ','.join(pk_values)

        try:
            name_string = '{}:'.format(self.name)
        except AttributeError:
            name_string = ''

        return "{class_name} ({name_string}{pk_string})".format(
            class_name=self.__class__.__name__,
            name_string=name_string,
            pk_string=pk_string,
        )

    def __str__(self):
        """
        Produces an in-depth string representation of the model including
        property details
        """
        sorted_props = [(k, self.props[k]) for k in sorted(self.props.keys())]
        return '\n    '.join(
            ['{}:'.format(repr(self))] +
            [
                '{}: {}'.format(k, getattr(self, k))
                for k in self.__table__.columns.keys()
            ]
        )


class AutoNameMixin:
    """
    This class provides a mixin that determines the tablename based on the
    class name. It uses the inflection module to compute it. It should only
    be used by classes that want the auto-naming behavior. Models that declare
    their own __tablename__ attribute should not use this mixin
    """

    @declared_attr
    def __tablename__(cls):
        return inflection.tableize(cls.__name__)


class Foo(ExampleBase):

    __tablename__ = 'foo'

    id = db.Column(db.BigInteger, primary_key=True)
    foo_type_id = db.Column(
        db.Integer, db.ForeignKey('foo_types.id'), index=True, nullable=False,
    )
    name = db.Column(db.Text)

    foo_type = db.relationship('FooType')

    @classmethod
    def foo_type_identity(cls):
        return inflection.underscore(cls.__name__)

    @declared_attr
    def __mapper_args__(cls):
        return dict(
            polymorphic_on=cls.foo_type_name_subquery(),
            polymorphic_identity=cls.foo_type_identity(),
        )

    @hybrid_property
    def foo_type_name(self):
        return self.foo_type.name

    @foo_type_name.setter
    def foo_type_name(self, value):
        self.foo_type_id = (
            select([FooType.id]).
            where(FooType.name == value).
            as_scalar()
        )

    @entity_type_name.expression
    def foo_type_name(cls):
        return cls.foo_type_name_subquery()

    @classmethod
    def foo_type_name_subquery(cls):
        return (
            select([FooType.name]).
            where(FooType.id == cls.foo_type_id).
            as_scalar()
        )

    class FooTypeNameComparator(Comparator):
        def operate(self, op, other):
            return op(
                Foo.foo_type_id,
                (
                    select([FooType.id]).
                    where(FooType.name == other).
                    as_scalar()
                ),
            )

    @foo_type_name.comparator
    def foo_type_name(cls):
        return cls.FooTypeNameComparator(cls)

    @classmethod
    def fetch_class_from_foo_type(cls, foo_type_id):
        foo_type_name = FooType.query.get(foo_type_id).name
        try:
            target_class = cls.__mapper__.polymorphic_map[foo_type_name].class_
        except KeyError:
            raise Buzz(
                "No foo subclass found for foo_type_id({}) named: {}",
                foo_type_id, foo_type_name,
            )
        return target_class

    @classmethod
    def make_foo(cls, **kwargs):

        if cls is Foo:
            foo_type_id = kwargs.pop('foo_type_id', None)
            entity_type = kwargs.pop('foo_type', None)
            Buzz.require_condition(
                (
                    (foo_type is not None and foo_type_id is None) or
                    (foo_type_id is not None and foo_type is None)
                ),
                "Must have foo_type xor foo_type_id",
            )
            target_class = cls.fetch_class_from_foo_type(foo_type_id or foo_type.id)
            return target_class(**kwargs)

        else:
            Buzz.require_condition(
                'foo_type' not in props and 'foo_type_id' not in props,
                "May not have foo_type or foo_type_id",
            )
            return super()(**kwargs)

    @classproperty
    def cls_entity_type(cls):
        """
        This is just a helper method that can fetch the EntityType instance
        that is associated with an Entity class.
        """
        return FooType.query.filter_by(name=cls.foo_type_identity).one_or_none()
