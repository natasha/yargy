from yargy.interpretation.fact import FactDefinition, Fact
from yargy.interpretation.attribute import Attribute


def test_smoke_subclass():
    class FactCls(FactDefinition):
        a: str
        b: str

    assert issubclass(FactCls, Fact)


def test_smoke_is_attribute():
    class FactCls(FactDefinition):
        a: str
        b: str

    assert isinstance(FactCls.a, Attribute)
    assert isinstance(FactCls.b, Attribute)
