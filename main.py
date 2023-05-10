import os
from urllib.parse import urlparse

import click
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.document_loaders.sitemap import SitemapLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import Chroma
from yaspin import yaspin

openai_models = [
    "gpt-4",
    "gpt-4-0314",
    "gpt-4-32k",
    "gpt-4-32k-0314",
    "gpt-3.5-turbo",
    "gpt-3.5-turbo-0301",
    "text-davinci-003",
    "text-davinci-002",
]


def validate_url(ctx, param, value):
    try:
        result = urlparse(value)
        # Check if the URL is valid by examining its scheme and netloc.
        if all([result.scheme, result.netloc]):
            return value
        else:
            raise ValueError
    except ValueError:
        raise click.BadParameter("Invalid URL")


def validate_sitemap(ctx, param, value):
    # Ensure the URL is valid and ends with sitemap.xml
    url = validate_url(ctx, param, value)
    if not ("sitemap" in url or url.endswith("xml")):
        raise click.BadParameter("URL must be a sitemap.xml URL")
    return url


def styled_prompt(text):
    return click.style(text, fg="green")


class ChatAnySite:
    def __init__(self, open_api_key, sitemap_url, model):
        self.open_api_key = open_api_key
        self.sitemap_url = sitemap_url
        self.model = model
        self.docsearch = self.load_sites(sitemap_url)
        self.qa = RetrievalQA.from_chain_type(
            llm=ChatOpenAI(
                openai_api_key=open_api_key,
                model_name=model,
            ),
            chain_type="stuff",
            retriever=self.docsearch.as_retriever(),
        )

    @staticmethod
    def load_sites(sitemap_url):
        sitemap_loader = SitemapLoader(web_path=sitemap_url)
        pages = sitemap_loader.load()
        text_splitter = CharacterTextSplitter()
        texts = text_splitter.split_documents(pages)
        embeddings = OpenAIEmbeddings()
        return Chroma.from_documents(texts, embeddings)

    @staticmethod
    def formatted_chat_response(text):
        click.echo(styled_prompt("Response"), nl=False)
        click.echo(": ", nl=False)
        click.echo(text)

    def chat(self):
        query = click.prompt(styled_prompt("Question"))
        with yaspin():
            response = self.qa.run(query)
        self.formatted_chat_response(response)

    def start_chat(self):
        while True:
            self.chat()


@click.command()
@click.option(
    "--open-api-key",
    prompt=styled_prompt("OpenAI API Key"),
    # default=lambda: os.environ.get("OPENAI_API_KEY", ""),
    hide_input=True,
    help="https://help.openai.com/en/articles/4936850-where-do-i-find-my-secret-api-key",
)
@click.option(
    "--sitemap-url",
    prompt=styled_prompt("Website sitemap.xml"),
    callback=validate_sitemap,
    help="A valid sitemap.xml URL",
)
@click.option(
    "--model",
    prompt=styled_prompt("LLM Model Name"),
    default=openai_models[0],
    type=click.Choice(openai_models, case_sensitive=False),
    help="https://platform.openai.com/docs/models",
)
def main(open_api_key, sitemap_url, model):
    chatbot = ChatAnySite(open_api_key, sitemap_url, model)
    chatbot.start_chat()


if __name__ == "__main__":
    main()
