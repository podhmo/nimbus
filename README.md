# nimbus

display object作成用のライブラリ

- display object
- validatable (display) object

## display object?

プレゼンテーションロジックを書きやすくするための中間表現。

### 例

以下のようなperson objectがある時

```py
class Person(object):
    def __init__(self, name, age, gender):
        self.name = name
        self.age = age
        self.gender = gender
```

以下のようなtemplateでレンダリングしたい。

```html
<dl>
<dt>名前</dt><dd>{{person.name}}</dd>
<dt>年齢</dt><dd>{{person.age}}</dd>
<dt>性別</dt><dd>{{person.gender|humanize}}</dd>
</dl>
```

以下の事柄が必要になってしまっている。

- 「名前、年齢、性別」などの人間のための属性名
- (オブジェクトの属性に順序はないが)「名前、年齢、性別」の順で列挙

display objectを使うと以下の様にして書くことができる

```html
<dl>
%for f in target:
  <dt>{{f.label}}</dt><dd>{{f.mapped}}</dd>
%endfor
</dl>
```

## 使い方

```py
class Person(object):
    def __init__(self, name, age, gender):
        self.name = name
        self.age = age
        self.gender = gender


def humanize(v):
    return "Female"  # xxx:


class PersonDisplay(MonitoringDisplay):
    name = display_property("name", label=u"名前")
    age = display_property("age", label=u"年齢")
    gender = display_property("gender", label=u"性別", mapping=humanize)  # xxx:


template = """
<dl>
%for f in target:
  <dt>{{f.label}}</dt><dd>{{f.value}}</dd>
%endfor
</dl>
"""

person = Person("foo", 20, "F")
pd = PersonDisplay(person)

render(template, person=pd)

# <dl>
# <dt>名前</dt><dd>foo</dd>
# <dt>年齢</dt><dd>20</dd>
# <dt>性別</dt><dd>Female</dd>
# </dl>
```

## 変わった使い方

### 構造をフラットにする

```py
class Foo(object):
    def __init__(self, name, boo):
        self.name = name
        self.boo = boo


class Boo(object):
    def __init__(self, name):
        self.name = name


class FooDisplay(MonitoringDisplay):
    foo_name = display_property("name", label="FooName")
    boo_name = display_property("boo.name", label="BooName")


foo = Foo("foo", Boo("boo"))
foo_display = FooDisplay(foo)
print("Label={} name={}".format(foo_display.foo_name.label,
                                foo_display.foo_name.value))  # => Label=FooName name=foo
print("Label={} name={}".format(foo_display.boo_name.label,
                                foo_display.boo_name.value))  # => Label=BooName name=boo
```

### エラー内容を各属性に注入する

```py
pd = PersonDisplay(person)
pd.inject("error", {"name": "booo"})
print(pd.name.error) # => boo
```

### 属性がオブジェクトなオブジェクト

```py
class Pair(object):
    def __init__(self, left, right):
        self.left = left
        self.right = right


class PairDisplay(MonitoringDisplay):
    left = display_property("left", label="Left", mapping=PersonDisplay)
    right = display_property("right", label="Right", mapping=PersonDisplay)

pair_display = PairDisplay(person, Person("bar",30,"F"))
pair_display.left.label # => "Left"
pair_display.left.value.name.value # => "foo"
pair_display.right.value.name.value # => "bar"
```

### 親-子関係(1:N)を持つオブジェクト

```py
class Team(object):
    def __init__(self, members):
        self.members = members


class TeamDisplay(MonitoringDisplay):
    member = display_property("members", label="Members", mapping=list_display(PersonDisplay))


team = Team([person, person, person])
team_display = TeamDisplay(team)
for p in team_display.member.value:
    print(p) #person
```

## validatable object

Formオブジェクトのようなもの

```py
from nimbus.validators import Validation, ValidatableDisplay
from functools import partial

Int = Validation(int).message("not integer")
int_field = partial(field_property, validation=Int, widget="number", required=True, initial=0)
object_field = partial(field_property, validation=lambda v: v, required=True, initial="")

class PointForm(ValidatableDisplay):
    x = int_field("x", label="X")
    y = int_field("y", label="Y")
```

template中で主にformを作る際に使う。
```py
# form (GET)
pf = PointForm()
print("""
<form method="POST" action="#">
  <label>{form.x.label}<input name="{form.x.name}" value="{form.x.value}" type="{form.x.widget}"/></label>
  <label>{form.y.label}<input name="{form.y.name}" value="{form.y.value}" type="{form.y.widget}"/></label>
<form>
""".format(form=pf))

## output
# <form method="POST" action="#">
#   <label>X<input name="x" value="0" type="number"/></label>
#   <label>Y<input name="y" value="0" type="number"/></label>
# <form>
```

validation
```py
print(PointForm({"x": "10", "y": "20"}))
print(PointForm({"x": "10", "y": "20"}).validate())  # => True
print(PointForm({"x": "10", "y": "aa"}).validate())  # => False
```

エラー時の再レンダリング

```py
pf = PointForm({"x": "10", "y": "aa"})
assert pf.validate() is False

print("""
<form method="POST" action="#">
  {form.x.errors}{form.y.errors}
  <label>{form.x.label}<input name="{form.x.name}" value="{form.x.value}" type="{form.x.widget}"/></label>
  <label>{form.y.label}<input name="{form.y.name}" value="{form.y.value}" type="{form.y.widget}"/></label>
<form>
""".format(form=pf))

## output
# <form method="POST" action="#">
#   []['not integer']
#   <label>X<input name="x" value="10" type="number"/></label>
#   <label>Y<input name="y" value="aa" type="number"/></label>
# <form>
```

ネストしたdictからformを生成

```
class PairForm(ValidatableDisplay):
    left = object_field("left", label="Left", mapping=PointForm)
    right = object_field("right", label="Right", mapping=PointForm)


ptform = PairForm({"left": {"x": "10", "y": "20"}, "right": {"x": "100", "y": "20@"}})

assert ptform.validate() is False
print("""
<form method="POST" action="#">
  {lform.x.errors}{lform.y.errors}  {rform.x.errors}{rform.y.errors}
  <label>{lform.x.label}<input name="{lform.x.name}" value="{lform.x.value}" type="{lform.x.widget}"/></label>
  <label>{lform.y.label}<input name="{lform.y.name}" value="{lform.y.value}" type="{lform.y.widget}"/></label>
  <label>{rform.x.label}<input name="{rform.x.name}" value="{rform.x.value}" type="{rform.x.widget}"/></label>
  <label>{rform.y.label}<input name="{rform.y.name}" value="{rform.y.value}" type="{rform.y.widget}"/></label>
<form>
""".format(lform=ptform.left.value, rform=ptform.right.value))

## output
# <form method="POST" action="#">
#   [][]  []['not integer']
#   <label>X<input name="x" value="10" type="number"/></label>
#   <label>Y<input name="y" value="20" type="number"/></label>
#   <label>X<input name="x" value="100" type="number"/></label>
#   <label>Y<input name="y" value="20@" type="number"/></label>
# <form>
```