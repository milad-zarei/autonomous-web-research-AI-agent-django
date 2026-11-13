from django import forms


class QuestionForm(forms.Form):
    question = forms.CharField(
        label="Your question",
        min_length=5,
        max_length=500,
        widget=forms.Textarea(
            attrs={"rows": 3, "dir": "auto", "placeholder": "What do you want to find out?"}
        ),
    )
