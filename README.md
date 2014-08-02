# nimbus

display object作成用のライブラリ

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


class PersonDisplay(Display):
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