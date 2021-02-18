from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from flask_wtf.file import FileField, FileAllowed
from wtforms.fields.html5 import DateField
from wtforms.widgets import TextArea
from wtforms.validators import (DataRequired, Length, 
                                ValidationError)
from datetime import datetime as dt

class TaskForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(),
                        Length(min=1, max=60)])
    due_date = DateField("Due Date", format='%Y-%m-%d',
                         validators=[DataRequired()])
    image = FileField("Add an Image",
                      validators=[FileAllowed(['png', 'jpg'])])
    status = SelectField("Task Status", choices=["Incomplete", 
                         "Complete"], validators=[DataRequired()])
    content = StringField("Content", widget=TextArea())
    submit = SubmitField("Create Task")

    def validate_due_date(self, due_date):
        # self.due_date.date = YYYY-mm-dd
        if self.status == "Complete":
            return True
        if due_date.data < dt.now().date():
             raise ValidationError("Cannot select a due date"\
                                   "from the past")
        return True
