<p align="center">
  <a href="#" target="blank"><img src="docs/img/EllarLogoIconOnly.png" width="200" alt="Ellar Logo" /></a>
</p>

<p align="center">Traditional Form package integrated with Pydantic models for an Ellar python web framework</p>

![Test](https://github.com/python-ellar/ellar-form/actions/workflows/test_full.yml/badge.svg)
![Coverage](https://img.shields.io/codecov/c/github/python-ellar/ellar-form)
[![PyPI version](https://badge.fury.io/py/ellar-form.svg)](https://badge.fury.io/py/ellar-form)
[![PyPI version](https://img.shields.io/pypi/v/ellar-form.svg)](https://pypi.python.org/pypi/ellar-form)
[![PyPI version](https://img.shields.io/pypi/pyversions/ellar-form.svg)](https://pypi.python.org/pypi/ellar-form)


## Introduction

Ellar-Form is a powerful and flexible form design package that seamlessly integrates with Pydantic models and the Ellar web framework. It comes with Pydantic field validation and can easily be rendered to HTML.

Key features of Ellar-Form include:
1. **Pydantic Integration**: Leverages Pydantic models for form field definitions and validation.
2. **Ellar Compatibility**: Designed to work seamlessly with Ellar's routing and request handling system.
3. **Automatic Form Generation**: Can automatically generate form fields from Pydantic models.
4. **Flexible Rendering**: Supports custom HTML templates for form field rendering.

Ellar-Form bridges the gap between Ellar web framework capabilities 
and the need for traditional form handling in web applications.

## Installation
To install Ellar-Form, simply use pip:

```bash
pip install ellar-form
```

## Usage
The following example demonstrates how to use Ellar-Form to handle form data in an Ellar application:
### ZForm Example
ZForm provides a convenient way to define and handle forms in your Ellar applications. Here's an example of how to use ZForm:

```python
from pydantic import BaseModel, EmailStr
from ellar.common import ModuleRouter, render_template
from zform import ZForm

class UserFormModel(BaseModel):
    password: str
    email: EmailStr

router = ModuleRouter('/')

@router.http_route("login", methods=["post", "get"])
def login(form: ZForm[UserFormModel]):
    if form.validate():
        return render_template("successful.html")

    return render_template("login.html", form=form)
```

In this example, we define a UserFormModel using Pydantic, which automatically creates corresponding form fields. The ZForm[UserFormModel] parameter in the route handler creates a form instance that can be validated and processed.

### FormManager Example
For more control over form processing, you can use the FormManager directly:

```python
from ellar.common import ModuleRouter, IExecutionContext, render_template
from zform import FormManager

router = ModuleRouter('/')

@router.http_route("login/another", methods=["post", "get"])
async def login_another(ctx: IExecutionContext):
    form = FormManager.from_schema(UserFormModel,ctx=ctx)
    
    if await form.validate():
        return render_template("successful.html")

    return render_template("login.html", form=form)
```

In this example, we define a UserFormModel using Pydantic, which automatically creates corresponding form fields. The ZForm[UserFormModel] parameter in the route handler creates a form instance that can be validated and processed.

### Form Templates Rendering
Ellar-Form provides customizable HTML templates for rendering form fields. Here's an example of a custom form template:

```html
 <form method="post" action="/form">
        <table>
            {% for field in form %}
                <tr>
                    <th>{{ field.label }}</th>
                    <td>{{ field }}</td>
                </tr>
            {% endfor %}
        </table>
        <button type="submit">Submit</button>
    </form>
```

When there is an error in the form, the template will render the error messages:

```html
<form method="post" action="/form">
    <table>
        {% for field in form %}
            <tr>
                <th>{{ field.label }}</th>
                <td>{{ field }}</td>
                {% if field.errors %}
                    <td class="error">{{ field.errors[0] }}</td>
                {% endif %}
            </tr>
        {% endfor %}
    </table>
    <button type="submit">Submit</button>
</form>
```

## Contributing
We welcome contributions to Ellar-Form! If you have suggestions or improvements, please open an issue or submit a pull request.

## License
This project is licensed under the MIT License. See the LICENSE file for details.
