import webbrowser
from openai import Model, Completion, Image
from dotenv import load_dotenv

load_dotenv()

# List available models
models = Model.list()
print(models)

# Text completions
completion = Completion.create(
    model="davinci",
    prompt="Steve Jobs was an American entrepreneur and inventor. List his greatest technology achievements.",
    temperature=0.5,
)
print(completion.choices[0].text)

# Image generation
images = Image.create(
    # file=open("images/steve-jobs.jpg", "rb"),
    size="512x512",
    prompt="Cartoon of a computer hacker writing a cool app.",
)
webbrowser.open_new_tab(images.data[0].url)